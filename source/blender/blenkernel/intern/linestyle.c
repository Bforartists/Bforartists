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
 * The Original Code is Copyright (C) 2010 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/linestyle.c
 *  \ingroup bke
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_material_types.h" /* for ramp blend */
#include "DNA_texture_types.h"

#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_linestyle.h"
#include "BKE_main.h"
#include "BKE_texture.h"
#include "BKE_colortools.h"
#include "BKE_animsys.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"

static const char *modifier_name[LS_MODIFIER_NUM] = {
	NULL,
	"Along Stroke",
	"Distance from Camera",
	"Distance from Object",
	"Material",
	"Sampling",
	"Bezier Curve",
	"Sinus Displacement",
	"Spatial Noise",
	"Perlin Noise 1D",
	"Perlin Noise 2D",
	"Backbone Stretcher",
	"Tip Remover",
	"Calligraphy",
	"Polygonalization",
	"Guiding Lines",
	"Blueprint",
	"2D Offset",
	"2D Transform",
};

static void default_linestyle_settings(FreestyleLineStyle *linestyle)
{
	linestyle->panel = LS_PANEL_STROKES;
	linestyle->r = linestyle->g = linestyle->b = 0.0f;
	linestyle->alpha = 1.0f;
	linestyle->thickness = 1.0f;
	linestyle->thickness_position = LS_THICKNESS_CENTER;
	linestyle->thickness_ratio = 0.5f;
	linestyle->chaining = LS_CHAINING_PLAIN;
	linestyle->rounds = 3;
	linestyle->min_angle = DEG2RADF(0.0f);
	linestyle->max_angle = DEG2RADF(0.0f);
	linestyle->min_length = 0.0f;
	linestyle->max_length = 10000.0f;
	linestyle->split_length = 100;

	linestyle->color_modifiers.first = linestyle->color_modifiers.last = NULL;
	linestyle->alpha_modifiers.first = linestyle->alpha_modifiers.last = NULL;
	linestyle->thickness_modifiers.first = linestyle->thickness_modifiers.last = NULL;
	linestyle->geometry_modifiers.first = linestyle->geometry_modifiers.last = NULL;

	FRS_add_linestyle_geometry_modifier(linestyle, LS_MODIFIER_SAMPLING);

	linestyle->caps = LS_CAPS_BUTT;
}

FreestyleLineStyle *FRS_new_linestyle(const char *name, struct Main *main)
{
	FreestyleLineStyle *linestyle;

	if (!main)
		main = G.main;

	linestyle = (FreestyleLineStyle *)BKE_libblock_alloc(&main->linestyle, ID_LS, name);

	default_linestyle_settings(linestyle);

	return linestyle;
}

void FRS_free_linestyle(FreestyleLineStyle *linestyle)
{
	LineStyleModifier *m;

	BKE_free_animdata(&linestyle->id);
	while ((m = (LineStyleModifier *)linestyle->color_modifiers.first))
		FRS_remove_linestyle_color_modifier(linestyle, m);
	while ((m = (LineStyleModifier *)linestyle->alpha_modifiers.first))
		FRS_remove_linestyle_alpha_modifier(linestyle, m);
	while ((m = (LineStyleModifier *)linestyle->thickness_modifiers.first))
		FRS_remove_linestyle_thickness_modifier(linestyle, m);
	while ((m = (LineStyleModifier *)linestyle->geometry_modifiers.first))
		FRS_remove_linestyle_geometry_modifier(linestyle, m);
}

FreestyleLineStyle *FRS_copy_linestyle(FreestyleLineStyle *linestyle)
{
	FreestyleLineStyle *new_linestyle;
	LineStyleModifier *m;

	new_linestyle = FRS_new_linestyle(linestyle->id.name + 2, NULL);
	FRS_free_linestyle(new_linestyle);

	new_linestyle->r = linestyle->r;
	new_linestyle->g = linestyle->g;
	new_linestyle->b = linestyle->b;
	new_linestyle->alpha = linestyle->alpha;
	new_linestyle->thickness = linestyle->thickness;
	new_linestyle->thickness_position = linestyle->thickness_position;
	new_linestyle->thickness_ratio = linestyle->thickness_ratio;
	new_linestyle->flag = linestyle->flag;
	new_linestyle->caps = linestyle->caps;
	new_linestyle->chaining = linestyle->chaining;
	new_linestyle->rounds = linestyle->rounds;
	new_linestyle->min_angle = linestyle->min_angle;
	new_linestyle->max_angle = linestyle->max_angle;
	new_linestyle->min_length = linestyle->min_length;
	new_linestyle->max_length = linestyle->max_length;
	new_linestyle->split_length = linestyle->split_length;
	new_linestyle->dash1 = linestyle->dash1;
	new_linestyle->gap1 = linestyle->gap1;
	new_linestyle->dash2 = linestyle->dash2;
	new_linestyle->gap2 = linestyle->gap2;
	new_linestyle->dash3 = linestyle->dash3;
	new_linestyle->gap3 = linestyle->gap3;
	new_linestyle->panel = linestyle->panel;
	for (m = (LineStyleModifier *)linestyle->color_modifiers.first; m; m = m->next)
		FRS_copy_linestyle_color_modifier(new_linestyle, m);
	for (m = (LineStyleModifier *)linestyle->alpha_modifiers.first; m; m = m->next)
		FRS_copy_linestyle_alpha_modifier(new_linestyle, m);
	for (m = (LineStyleModifier *)linestyle->thickness_modifiers.first; m; m = m->next)
		FRS_copy_linestyle_thickness_modifier(new_linestyle, m);
	for (m = (LineStyleModifier *)linestyle->geometry_modifiers.first; m; m = m->next)
		FRS_copy_linestyle_geometry_modifier(new_linestyle, m);

	return new_linestyle;
}

static LineStyleModifier *new_modifier(int type, size_t size)
{
	LineStyleModifier *m;

	m = (LineStyleModifier *)MEM_callocN(size, "line style modifier");
	if (m) {
		m->type = type;
		strcpy(m->name, modifier_name[type]);
		m->influence = 1.0f;
		m->flags = LS_MODIFIER_ENABLED | LS_MODIFIER_EXPANDED;
	}

	return m;
}

static void add_to_modifier_list(ListBase *lb, LineStyleModifier *m)
{
	BLI_addtail(lb, (void *)m);
	BLI_uniquename(lb, m, modifier_name[m->type], '.', offsetof(LineStyleModifier, name), sizeof(m->name));
}

static LineStyleModifier *alloc_color_modifier(int type)
{
	size_t size;

	switch (type) {
	case LS_MODIFIER_ALONG_STROKE:
		size = sizeof(LineStyleColorModifier_AlongStroke);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		size = sizeof(LineStyleColorModifier_DistanceFromCamera);
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		size = sizeof(LineStyleColorModifier_DistanceFromObject);
		break;
	case LS_MODIFIER_MATERIAL:
		size = sizeof(LineStyleColorModifier_Material);
		break;
	default:
		return NULL; /* unknown modifier type */
	}

	return new_modifier(type, size);
}

LineStyleModifier *FRS_add_linestyle_color_modifier(FreestyleLineStyle *linestyle, int type)
{
	LineStyleModifier *m;

	m = alloc_color_modifier(type);
	if (!m)
		return NULL;
	m->blend = MA_RAMP_BLEND;

	switch (type) {
	case LS_MODIFIER_ALONG_STROKE:
		((LineStyleColorModifier_AlongStroke *)m)->color_ramp = add_colorband(1);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		((LineStyleColorModifier_DistanceFromCamera *)m)->color_ramp = add_colorband(1);
		((LineStyleColorModifier_DistanceFromCamera *)m)->range_min = 0.0f;
		((LineStyleColorModifier_DistanceFromCamera *)m)->range_max = 10000.0f;
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		((LineStyleColorModifier_DistanceFromObject *)m)->target = NULL;
		((LineStyleColorModifier_DistanceFromObject *)m)->color_ramp = add_colorband(1);
		((LineStyleColorModifier_DistanceFromObject *)m)->range_min = 0.0f;
		((LineStyleColorModifier_DistanceFromObject *)m)->range_max = 10000.0f;
		break;
	case LS_MODIFIER_MATERIAL:
		((LineStyleColorModifier_Material *)m)->color_ramp = add_colorband(1);
		((LineStyleColorModifier_Material *)m)->mat_attr = LS_MODIFIER_MATERIAL_DIFF;
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->color_modifiers, m);

	return m;
}

LineStyleModifier *FRS_copy_linestyle_color_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	LineStyleModifier *new_m;

	new_m = alloc_color_modifier(m->type);
	if (!new_m)
		return NULL;
	new_m->influence = m->influence;
	new_m->flags = m->flags;
	new_m->blend = m->blend;

	switch (m->type) {
	case LS_MODIFIER_ALONG_STROKE:
		{
			LineStyleColorModifier_AlongStroke *p = (LineStyleColorModifier_AlongStroke *)m;
			((LineStyleColorModifier_AlongStroke *)new_m)->color_ramp = MEM_dupallocN(p->color_ramp);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		{
			LineStyleColorModifier_DistanceFromCamera *p = (LineStyleColorModifier_DistanceFromCamera *)m;
			((LineStyleColorModifier_DistanceFromCamera *)new_m)->color_ramp = MEM_dupallocN(p->color_ramp);
			((LineStyleColorModifier_DistanceFromCamera *)new_m)->range_min = p->range_min;
			((LineStyleColorModifier_DistanceFromCamera *)new_m)->range_max = p->range_max;
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		{
			LineStyleColorModifier_DistanceFromObject *p = (LineStyleColorModifier_DistanceFromObject *)m;
			if (p->target)
				p->target->id.us++;
			((LineStyleColorModifier_DistanceFromObject *)new_m)->target = p->target;
			((LineStyleColorModifier_DistanceFromObject *)new_m)->color_ramp = MEM_dupallocN(p->color_ramp);
			((LineStyleColorModifier_DistanceFromObject *)new_m)->range_min = p->range_min;
			((LineStyleColorModifier_DistanceFromObject *)new_m)->range_max = p->range_max;
		}
		break;
	case LS_MODIFIER_MATERIAL:
		{
			LineStyleColorModifier_Material *p = (LineStyleColorModifier_Material *)m;
			((LineStyleColorModifier_Material *)new_m)->color_ramp = MEM_dupallocN(p->color_ramp);
			((LineStyleColorModifier_Material *)new_m)->mat_attr = p->mat_attr;
		}
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->color_modifiers, new_m);

	return new_m;
}

void FRS_remove_linestyle_color_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	switch (m->type) {
	case LS_MODIFIER_ALONG_STROKE:
		MEM_freeN(((LineStyleColorModifier_AlongStroke *)m)->color_ramp);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		MEM_freeN(((LineStyleColorModifier_DistanceFromCamera *)m)->color_ramp);
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		MEM_freeN(((LineStyleColorModifier_DistanceFromObject *)m)->color_ramp);
		break;
	case LS_MODIFIER_MATERIAL:
		MEM_freeN(((LineStyleColorModifier_Material *)m)->color_ramp);
		break;
	}
	BLI_freelinkN(&linestyle->color_modifiers, m);
}

static LineStyleModifier *alloc_alpha_modifier(int type)
{
	size_t size;

	switch (type) {
	case LS_MODIFIER_ALONG_STROKE:
		size = sizeof(LineStyleAlphaModifier_AlongStroke);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		size = sizeof(LineStyleAlphaModifier_DistanceFromCamera);
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		size = sizeof(LineStyleAlphaModifier_DistanceFromObject);
		break;
	case LS_MODIFIER_MATERIAL:
		size = sizeof(LineStyleAlphaModifier_Material);
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	return new_modifier(type, size);
}

LineStyleModifier *FRS_add_linestyle_alpha_modifier(FreestyleLineStyle *linestyle, int type)
{
	LineStyleModifier *m;

	m = alloc_alpha_modifier(type);
	if (!m)
		return NULL;
	m->blend = LS_VALUE_BLEND;

	switch (type) {
	case LS_MODIFIER_ALONG_STROKE:
		((LineStyleAlphaModifier_AlongStroke *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		((LineStyleAlphaModifier_DistanceFromCamera *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleAlphaModifier_DistanceFromCamera *)m)->range_min = 0.0f;
		((LineStyleAlphaModifier_DistanceFromCamera *)m)->range_max = 10000.0f;
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		((LineStyleAlphaModifier_DistanceFromObject *)m)->target = NULL;
		((LineStyleAlphaModifier_DistanceFromObject *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleAlphaModifier_DistanceFromObject *)m)->range_min = 0.0f;
		((LineStyleAlphaModifier_DistanceFromObject *)m)->range_max = 10000.0f;
		break;
	case LS_MODIFIER_MATERIAL:
		((LineStyleAlphaModifier_Material *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleAlphaModifier_Material *)m)->mat_attr = LS_MODIFIER_MATERIAL_DIFF;
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->alpha_modifiers, m);

	return m;
}

LineStyleModifier *FRS_copy_linestyle_alpha_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	LineStyleModifier *new_m;

	new_m = alloc_alpha_modifier(m->type);
	if (!new_m)
		return NULL;
	new_m->influence = m->influence;
	new_m->flags = m->flags;
	new_m->blend = m->blend;

	switch (m->type) {
	case LS_MODIFIER_ALONG_STROKE:
		{
			LineStyleAlphaModifier_AlongStroke *p = (LineStyleAlphaModifier_AlongStroke *)m;
			((LineStyleAlphaModifier_AlongStroke *)new_m)->curve = curvemapping_copy(p->curve);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		{
			LineStyleAlphaModifier_DistanceFromCamera *p = (LineStyleAlphaModifier_DistanceFromCamera *)m;
			((LineStyleAlphaModifier_DistanceFromCamera *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleAlphaModifier_DistanceFromCamera *)new_m)->range_min = p->range_min;
			((LineStyleAlphaModifier_DistanceFromCamera *)new_m)->range_max = p->range_max;
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		{
			LineStyleAlphaModifier_DistanceFromObject *p = (LineStyleAlphaModifier_DistanceFromObject *)m;
			if (p->target)
				p->target->id.us++;
			((LineStyleAlphaModifier_DistanceFromObject *)new_m)->target = p->target;
			((LineStyleAlphaModifier_DistanceFromObject *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleAlphaModifier_DistanceFromObject *)new_m)->range_min = p->range_min;
			((LineStyleAlphaModifier_DistanceFromObject *)new_m)->range_max = p->range_max;
		}
		break;
	case LS_MODIFIER_MATERIAL:
		{
			LineStyleAlphaModifier_Material *p = (LineStyleAlphaModifier_Material *)m;
			((LineStyleAlphaModifier_Material *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleAlphaModifier_Material *)new_m)->mat_attr = p->mat_attr;
		}
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->alpha_modifiers, new_m);

	return new_m;
}

void FRS_remove_linestyle_alpha_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	switch (m->type) {
	case LS_MODIFIER_ALONG_STROKE:
		curvemapping_free(((LineStyleAlphaModifier_AlongStroke *)m)->curve);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		curvemapping_free(((LineStyleAlphaModifier_DistanceFromCamera *)m)->curve);
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		curvemapping_free(((LineStyleAlphaModifier_DistanceFromObject *)m)->curve);
		break;
	case LS_MODIFIER_MATERIAL:
		curvemapping_free(((LineStyleAlphaModifier_Material *)m)->curve);
		break;
	}
	BLI_freelinkN(&linestyle->alpha_modifiers, m);
}

static LineStyleModifier *alloc_thickness_modifier(int type)
{
	size_t size;

	switch (type) {
	case LS_MODIFIER_ALONG_STROKE:
		size = sizeof(LineStyleThicknessModifier_AlongStroke);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		size = sizeof(LineStyleThicknessModifier_DistanceFromCamera);
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		size = sizeof(LineStyleThicknessModifier_DistanceFromObject);
		break;
	case LS_MODIFIER_MATERIAL:
		size = sizeof(LineStyleThicknessModifier_Material);
		break;
	case LS_MODIFIER_CALLIGRAPHY:
		size = sizeof(LineStyleThicknessModifier_Calligraphy);
		break;
	default:
		return NULL; /* unknown modifier type */
	}

	return new_modifier(type, size);
}

LineStyleModifier *FRS_add_linestyle_thickness_modifier(FreestyleLineStyle *linestyle, int type)
{
	LineStyleModifier *m;

	m = alloc_thickness_modifier(type);
	if (!m)
		return NULL;
	m->blend = LS_VALUE_BLEND;

	switch (type) {
	case LS_MODIFIER_ALONG_STROKE:
		((LineStyleThicknessModifier_AlongStroke *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleThicknessModifier_AlongStroke *)m)->value_min = 0.0f;
		((LineStyleThicknessModifier_AlongStroke *)m)->value_max = 1.0f;
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		((LineStyleThicknessModifier_DistanceFromCamera *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleThicknessModifier_DistanceFromCamera *)m)->range_min = 0.0f;
		((LineStyleThicknessModifier_DistanceFromCamera *)m)->range_max = 1000.0f;
		((LineStyleThicknessModifier_DistanceFromCamera *)m)->value_min = 0.0f;
		((LineStyleThicknessModifier_DistanceFromCamera *)m)->value_max = 1.0f;
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		((LineStyleThicknessModifier_DistanceFromObject *)m)->target = NULL;
		((LineStyleThicknessModifier_DistanceFromObject *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleThicknessModifier_DistanceFromObject *)m)->range_min = 0.0f;
		((LineStyleThicknessModifier_DistanceFromObject *)m)->range_max = 1000.0f;
		((LineStyleThicknessModifier_DistanceFromObject *)m)->value_min = 0.0f;
		((LineStyleThicknessModifier_DistanceFromObject *)m)->value_max = 1.0f;
		break;
	case LS_MODIFIER_MATERIAL:
		((LineStyleThicknessModifier_Material *)m)->curve = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
		((LineStyleThicknessModifier_Material *)m)->mat_attr = LS_MODIFIER_MATERIAL_DIFF;
		((LineStyleThicknessModifier_Material *)m)->value_min = 0.0f;
		((LineStyleThicknessModifier_Material *)m)->value_max = 1.0f;
		break;
	case LS_MODIFIER_CALLIGRAPHY:
		((LineStyleThicknessModifier_Calligraphy *)m)->min_thickness = 1.0f;
		((LineStyleThicknessModifier_Calligraphy *)m)->max_thickness = 10.0f;
		((LineStyleThicknessModifier_Calligraphy *)m)->orientation = DEG2RADF(60.0f);
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->thickness_modifiers, m);

	return m;
}

LineStyleModifier *FRS_copy_linestyle_thickness_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	LineStyleModifier *new_m;

	new_m = alloc_thickness_modifier(m->type);
	if (!new_m)
		return NULL;
	new_m->influence = m->influence;
	new_m->flags = m->flags;
	new_m->blend = m->blend;

	switch (m->type) {
	case LS_MODIFIER_ALONG_STROKE:
		{
			LineStyleThicknessModifier_AlongStroke *p = (LineStyleThicknessModifier_AlongStroke *)m;
			((LineStyleThicknessModifier_AlongStroke *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleThicknessModifier_AlongStroke *)new_m)->value_min = p->value_min;
			((LineStyleThicknessModifier_AlongStroke *)new_m)->value_max = p->value_max;
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		{
			LineStyleThicknessModifier_DistanceFromCamera *p = (LineStyleThicknessModifier_DistanceFromCamera *)m;
			((LineStyleThicknessModifier_DistanceFromCamera *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleThicknessModifier_DistanceFromCamera *)new_m)->range_min = p->range_min;
			((LineStyleThicknessModifier_DistanceFromCamera *)new_m)->range_max = p->range_max;
			((LineStyleThicknessModifier_DistanceFromCamera *)new_m)->value_min = p->value_min;
			((LineStyleThicknessModifier_DistanceFromCamera *)new_m)->value_max = p->value_max;
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		{
			LineStyleThicknessModifier_DistanceFromObject *p = (LineStyleThicknessModifier_DistanceFromObject *)m;
			if (p->target)
				p->target->id.us++;
			((LineStyleThicknessModifier_DistanceFromObject *)new_m)->target = p->target;
			((LineStyleThicknessModifier_DistanceFromObject *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleThicknessModifier_DistanceFromObject *)new_m)->range_min = p->range_min;
			((LineStyleThicknessModifier_DistanceFromObject *)new_m)->range_max = p->range_max;
			((LineStyleThicknessModifier_DistanceFromObject *)new_m)->value_min = p->value_min;
			((LineStyleThicknessModifier_DistanceFromObject *)new_m)->value_max = p->value_max;
		}
		break;
	case LS_MODIFIER_MATERIAL:
		{
			LineStyleThicknessModifier_Material *p = (LineStyleThicknessModifier_Material *)m;
			((LineStyleThicknessModifier_Material *)new_m)->curve = curvemapping_copy(p->curve);
			((LineStyleThicknessModifier_Material *)new_m)->mat_attr = p->mat_attr;
			((LineStyleThicknessModifier_Material *)new_m)->value_min = p->value_min;
			((LineStyleThicknessModifier_Material *)new_m)->value_max = p->value_max;
		}
		break;
	case LS_MODIFIER_CALLIGRAPHY:
		{
			LineStyleThicknessModifier_Calligraphy *p = (LineStyleThicknessModifier_Calligraphy *)m;
			((LineStyleThicknessModifier_Calligraphy *)new_m)->min_thickness = p->min_thickness;
			((LineStyleThicknessModifier_Calligraphy *)new_m)->max_thickness = p->max_thickness;
			((LineStyleThicknessModifier_Calligraphy *)new_m)->orientation = p->orientation;
		}
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->thickness_modifiers, new_m);

	return new_m;
}

void FRS_remove_linestyle_thickness_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	switch (m->type) {
	case LS_MODIFIER_ALONG_STROKE:
		curvemapping_free(((LineStyleThicknessModifier_AlongStroke *)m)->curve);
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		curvemapping_free(((LineStyleThicknessModifier_DistanceFromCamera *)m)->curve);
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		curvemapping_free(((LineStyleThicknessModifier_DistanceFromObject *)m)->curve);
		break;
	case LS_MODIFIER_MATERIAL:
		curvemapping_free(((LineStyleThicknessModifier_Material *)m)->curve);
		break;
	case LS_MODIFIER_CALLIGRAPHY:
		break;
	}
	BLI_freelinkN(&linestyle->thickness_modifiers, m);
}

static LineStyleModifier *alloc_geometry_modifier(int type)
{
	size_t size;

	switch (type) {
	case LS_MODIFIER_SAMPLING:
		size = sizeof(LineStyleGeometryModifier_Sampling);
		break;
	case LS_MODIFIER_BEZIER_CURVE:
		size = sizeof(LineStyleGeometryModifier_BezierCurve);
		break;
	case LS_MODIFIER_SINUS_DISPLACEMENT:
		size = sizeof(LineStyleGeometryModifier_SinusDisplacement);
		break;
	case LS_MODIFIER_SPATIAL_NOISE:
		size = sizeof(LineStyleGeometryModifier_SpatialNoise);
		break;
	case LS_MODIFIER_PERLIN_NOISE_1D:
		size = sizeof(LineStyleGeometryModifier_PerlinNoise1D);
		break;
	case LS_MODIFIER_PERLIN_NOISE_2D:
		size = sizeof(LineStyleGeometryModifier_PerlinNoise2D);
		break;
	case LS_MODIFIER_BACKBONE_STRETCHER:
		size = sizeof(LineStyleGeometryModifier_BackboneStretcher);
		break;
	case LS_MODIFIER_TIP_REMOVER:
		size = sizeof(LineStyleGeometryModifier_TipRemover);
		break;
	case LS_MODIFIER_POLYGONIZATION:
		size = sizeof(LineStyleGeometryModifier_Polygonalization);
		break;
	case LS_MODIFIER_GUIDING_LINES:
		size = sizeof(LineStyleGeometryModifier_GuidingLines);
		break;
	case LS_MODIFIER_BLUEPRINT:
		size = sizeof(LineStyleGeometryModifier_Blueprint);
		break;
	case LS_MODIFIER_2D_OFFSET:
		size = sizeof(LineStyleGeometryModifier_2DOffset);
		break;
	case LS_MODIFIER_2D_TRANSFORM:
		size = sizeof(LineStyleGeometryModifier_2DTransform);
		break;
	default:
		return NULL; /* unknown modifier type */
	}

	return new_modifier(type, size);
}

LineStyleModifier *FRS_add_linestyle_geometry_modifier(FreestyleLineStyle *linestyle, int type)
{
	LineStyleModifier *m;

	m = alloc_geometry_modifier(type);
	if (!m)
		return NULL;

	switch (type) {
	case LS_MODIFIER_SAMPLING:
		((LineStyleGeometryModifier_Sampling *)m)->sampling = 10.0f;
		break;
	case LS_MODIFIER_BEZIER_CURVE:
		((LineStyleGeometryModifier_BezierCurve *)m)->error = 10.0f;
		break;
	case LS_MODIFIER_SINUS_DISPLACEMENT:
		((LineStyleGeometryModifier_SinusDisplacement *)m)->wavelength = 20.0f;
		((LineStyleGeometryModifier_SinusDisplacement *)m)->amplitude = 5.0f;
		((LineStyleGeometryModifier_SinusDisplacement *)m)->phase = 0.0f;
		break;
	case LS_MODIFIER_SPATIAL_NOISE:
		((LineStyleGeometryModifier_SpatialNoise *)m)->amplitude = 5.0f;
		((LineStyleGeometryModifier_SpatialNoise *)m)->scale = 20.0f;
		((LineStyleGeometryModifier_SpatialNoise *)m)->octaves = 4;
		((LineStyleGeometryModifier_SpatialNoise *)m)->flags = LS_MODIFIER_SPATIAL_NOISE_SMOOTH | LS_MODIFIER_SPATIAL_NOISE_PURERANDOM;
		break;
	case LS_MODIFIER_PERLIN_NOISE_1D:
		((LineStyleGeometryModifier_PerlinNoise1D *)m)->frequency = 10.0f;
		((LineStyleGeometryModifier_PerlinNoise1D *)m)->amplitude = 10.0f;
		((LineStyleGeometryModifier_PerlinNoise1D *)m)->octaves = 4;
		((LineStyleGeometryModifier_PerlinNoise1D *)m)->angle = DEG2RADF(45.0f);
		break;
	case LS_MODIFIER_PERLIN_NOISE_2D:
		((LineStyleGeometryModifier_PerlinNoise2D *)m)->frequency = 10.0f;
		((LineStyleGeometryModifier_PerlinNoise2D *)m)->amplitude = 10.0f;
		((LineStyleGeometryModifier_PerlinNoise2D *)m)->octaves = 4;
		((LineStyleGeometryModifier_PerlinNoise2D *)m)->angle = DEG2RADF(45.0f);
		break;
	case LS_MODIFIER_BACKBONE_STRETCHER:
		((LineStyleGeometryModifier_BackboneStretcher *)m)->backbone_length = 10.0f;
		break;
	case LS_MODIFIER_TIP_REMOVER:
		((LineStyleGeometryModifier_TipRemover *)m)->tip_length = 10.0f;
		break;
	case LS_MODIFIER_POLYGONIZATION:
		((LineStyleGeometryModifier_Polygonalization *)m)->error = 10.0f;
		break;
	case LS_MODIFIER_GUIDING_LINES:
		((LineStyleGeometryModifier_GuidingLines *)m)->offset = 0.0f;
		break;
	case LS_MODIFIER_BLUEPRINT:
		((LineStyleGeometryModifier_Blueprint *)m)->flags = LS_MODIFIER_BLUEPRINT_CIRCLES;
		((LineStyleGeometryModifier_Blueprint *)m)->rounds = 1;
		((LineStyleGeometryModifier_Blueprint *)m)->backbone_length = 10.0f;
		((LineStyleGeometryModifier_Blueprint *)m)->random_radius = 3;
		((LineStyleGeometryModifier_Blueprint *)m)->random_center = 5;
		((LineStyleGeometryModifier_Blueprint *)m)->random_backbone = 5;
		break;
	case LS_MODIFIER_2D_OFFSET:
		((LineStyleGeometryModifier_2DOffset *)m)->start = 0.0f;
		((LineStyleGeometryModifier_2DOffset *)m)->end = 0.0f;
		((LineStyleGeometryModifier_2DOffset *)m)->x = 0.0f;
		((LineStyleGeometryModifier_2DOffset *)m)->y = 0.0f;
		break;
	case LS_MODIFIER_2D_TRANSFORM:
		((LineStyleGeometryModifier_2DTransform *)m)->pivot = LS_MODIFIER_2D_TRANSFORM_PIVOT_CENTER;
		((LineStyleGeometryModifier_2DTransform *)m)->scale_x = 1.0f;
		((LineStyleGeometryModifier_2DTransform *)m)->scale_y = 1.0f;
		((LineStyleGeometryModifier_2DTransform *)m)->angle = DEG2RADF(0.0f);
		((LineStyleGeometryModifier_2DTransform *)m)->pivot_u = 0.5f;
		((LineStyleGeometryModifier_2DTransform *)m)->pivot_x = 0.0f;
		((LineStyleGeometryModifier_2DTransform *)m)->pivot_y = 0.0f;
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->geometry_modifiers, m);

	return m;
}

LineStyleModifier *FRS_copy_linestyle_geometry_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	LineStyleModifier *new_m;

	new_m = alloc_geometry_modifier(m->type);
	if (!new_m)
		return NULL;
	new_m->flags = m->flags;

	switch (m->type) {
	case LS_MODIFIER_SAMPLING:
		{
			LineStyleGeometryModifier_Sampling *p = (LineStyleGeometryModifier_Sampling *)m;
			((LineStyleGeometryModifier_Sampling *)new_m)->sampling = p->sampling;
		}
		break;
	case LS_MODIFIER_BEZIER_CURVE:
		{
			LineStyleGeometryModifier_BezierCurve *p = (LineStyleGeometryModifier_BezierCurve *)m;
			((LineStyleGeometryModifier_BezierCurve *)new_m)->error = p->error;
		}
		break;
	case LS_MODIFIER_SINUS_DISPLACEMENT:
		{
			LineStyleGeometryModifier_SinusDisplacement *p = (LineStyleGeometryModifier_SinusDisplacement *)m;
			((LineStyleGeometryModifier_SinusDisplacement *)new_m)->wavelength = p->wavelength;
			((LineStyleGeometryModifier_SinusDisplacement *)new_m)->amplitude = p->amplitude;
			((LineStyleGeometryModifier_SinusDisplacement *)new_m)->phase = p->phase;
		}
		break;
	case LS_MODIFIER_SPATIAL_NOISE:
		{
			LineStyleGeometryModifier_SpatialNoise *p = (LineStyleGeometryModifier_SpatialNoise *)m;
			((LineStyleGeometryModifier_SpatialNoise *)new_m)->amplitude = p->amplitude;
			((LineStyleGeometryModifier_SpatialNoise *)new_m)->scale = p->scale;
			((LineStyleGeometryModifier_SpatialNoise *)new_m)->octaves = p->octaves;
			((LineStyleGeometryModifier_SpatialNoise *)new_m)->flags = p->flags;
		}
		break;
	case LS_MODIFIER_PERLIN_NOISE_1D:
		{
			LineStyleGeometryModifier_PerlinNoise1D *p = (LineStyleGeometryModifier_PerlinNoise1D *)m;
			((LineStyleGeometryModifier_PerlinNoise1D *)new_m)->frequency = p->frequency;
			((LineStyleGeometryModifier_PerlinNoise1D *)new_m)->amplitude = p->amplitude;
			((LineStyleGeometryModifier_PerlinNoise1D *)new_m)->octaves = p->octaves;
			((LineStyleGeometryModifier_PerlinNoise1D *)new_m)->angle = p->angle;
		}
		break;
	case LS_MODIFIER_PERLIN_NOISE_2D:
		{
			LineStyleGeometryModifier_PerlinNoise2D *p = (LineStyleGeometryModifier_PerlinNoise2D *)m;
			((LineStyleGeometryModifier_PerlinNoise2D *)new_m)->frequency = p->frequency;
			((LineStyleGeometryModifier_PerlinNoise2D *)new_m)->amplitude = p->amplitude;
			((LineStyleGeometryModifier_PerlinNoise2D *)new_m)->octaves = p->octaves;
			((LineStyleGeometryModifier_PerlinNoise2D *)new_m)->angle = p->angle;
		}
		break;
	case LS_MODIFIER_BACKBONE_STRETCHER:
		{
			LineStyleGeometryModifier_BackboneStretcher *p = (LineStyleGeometryModifier_BackboneStretcher *)m;
			((LineStyleGeometryModifier_BackboneStretcher *)new_m)->backbone_length = p->backbone_length;
		}
		break;
	case LS_MODIFIER_TIP_REMOVER:
		{
			LineStyleGeometryModifier_TipRemover *p = (LineStyleGeometryModifier_TipRemover *)m;
			((LineStyleGeometryModifier_TipRemover *)new_m)->tip_length = p->tip_length;
		}
		break;
	case LS_MODIFIER_POLYGONIZATION:
		{
			LineStyleGeometryModifier_Polygonalization *p = (LineStyleGeometryModifier_Polygonalization *)m;
			((LineStyleGeometryModifier_Polygonalization *)new_m)->error = p->error;
		}
		break;
	case LS_MODIFIER_GUIDING_LINES:
		{
			LineStyleGeometryModifier_GuidingLines *p = (LineStyleGeometryModifier_GuidingLines *)m;
			((LineStyleGeometryModifier_GuidingLines *)new_m)->offset = p->offset;
		}
		break;
	case LS_MODIFIER_BLUEPRINT:
		{
			LineStyleGeometryModifier_Blueprint *p = (LineStyleGeometryModifier_Blueprint *)m;
			((LineStyleGeometryModifier_Blueprint *)new_m)->flags = p->flags;
			((LineStyleGeometryModifier_Blueprint *)new_m)->rounds = p->rounds;
			((LineStyleGeometryModifier_Blueprint *)new_m)->backbone_length = p->backbone_length;
			((LineStyleGeometryModifier_Blueprint *)new_m)->random_radius = p->random_radius;
			((LineStyleGeometryModifier_Blueprint *)new_m)->random_center = p->random_center;
			((LineStyleGeometryModifier_Blueprint *)new_m)->random_backbone = p->random_backbone;
		}
		break;
	case LS_MODIFIER_2D_OFFSET:
		{
			LineStyleGeometryModifier_2DOffset *p = (LineStyleGeometryModifier_2DOffset *)m;
			((LineStyleGeometryModifier_2DOffset *)new_m)->start = p->start;
			((LineStyleGeometryModifier_2DOffset *)new_m)->end = p->end;
			((LineStyleGeometryModifier_2DOffset *)new_m)->x = p->x;
			((LineStyleGeometryModifier_2DOffset *)new_m)->y = p->y;
		}
		break;
	case LS_MODIFIER_2D_TRANSFORM:
		{
			LineStyleGeometryModifier_2DTransform *p = (LineStyleGeometryModifier_2DTransform *)m;
			((LineStyleGeometryModifier_2DTransform *)new_m)->pivot = p->pivot;
			((LineStyleGeometryModifier_2DTransform *)new_m)->scale_x = p->scale_x;
			((LineStyleGeometryModifier_2DTransform *)new_m)->scale_y = p->scale_y;
			((LineStyleGeometryModifier_2DTransform *)new_m)->angle = p->angle;
			((LineStyleGeometryModifier_2DTransform *)new_m)->pivot_u = p->pivot_u;
			((LineStyleGeometryModifier_2DTransform *)new_m)->pivot_x = p->pivot_x;
			((LineStyleGeometryModifier_2DTransform *)new_m)->pivot_y = p->pivot_y;
		}
		break;
	default:
		return NULL; /* unknown modifier type */
	}
	add_to_modifier_list(&linestyle->geometry_modifiers, new_m);

	return new_m;
}

void FRS_remove_linestyle_geometry_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *m)
{
	switch (m->type) {
	case LS_MODIFIER_SAMPLING:
		break;
	case LS_MODIFIER_BEZIER_CURVE:
		break;
	case LS_MODIFIER_SINUS_DISPLACEMENT:
		break;
	case LS_MODIFIER_SPATIAL_NOISE:
		break;
	case LS_MODIFIER_PERLIN_NOISE_1D:
		break;
	case LS_MODIFIER_PERLIN_NOISE_2D:
		break;
	case LS_MODIFIER_BACKBONE_STRETCHER:
		break;
	case LS_MODIFIER_TIP_REMOVER:
		break;
	case LS_MODIFIER_POLYGONIZATION:
		break;
	case LS_MODIFIER_GUIDING_LINES:
		break;
	case LS_MODIFIER_BLUEPRINT:
		break;
	case LS_MODIFIER_2D_OFFSET:
		break;
	case LS_MODIFIER_2D_TRANSFORM:
		break;
	}
	BLI_freelinkN(&linestyle->geometry_modifiers, m);
}

static void move_modifier(ListBase *lb, LineStyleModifier *modifier, int direction)
{
	BLI_remlink(lb, modifier);
	if (direction > 0)
		BLI_insertlinkbefore(lb, modifier->prev, modifier);
	else
		BLI_insertlinkafter(lb, modifier->next, modifier);
}

void FRS_move_linestyle_color_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *modifier, int direction)
{
	move_modifier(&linestyle->color_modifiers, modifier, direction);
}

void FRS_move_linestyle_alpha_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *modifier, int direction)
{
	move_modifier(&linestyle->alpha_modifiers, modifier, direction);
}

void FRS_move_linestyle_thickness_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *modifier, int direction)
{
	move_modifier(&linestyle->thickness_modifiers, modifier, direction);
}

void FRS_move_linestyle_geometry_modifier(FreestyleLineStyle *linestyle, LineStyleModifier *modifier, int direction)
{
	move_modifier(&linestyle->geometry_modifiers, modifier, direction);
}

void FRS_list_modifier_color_ramps(FreestyleLineStyle *linestyle, ListBase *listbase)
{
	LineStyleModifier *m;
	ColorBand *color_ramp;
	LinkData *link;

	listbase->first = listbase->last = NULL;
	for (m = (LineStyleModifier *)linestyle->color_modifiers.first; m; m = m->next) {
		switch (m->type) {
		case LS_MODIFIER_ALONG_STROKE:
			color_ramp = ((LineStyleColorModifier_AlongStroke *)m)->color_ramp;
			break;
		case LS_MODIFIER_DISTANCE_FROM_CAMERA:
			color_ramp = ((LineStyleColorModifier_DistanceFromCamera *)m)->color_ramp;
			break;
		case LS_MODIFIER_DISTANCE_FROM_OBJECT:
			color_ramp = ((LineStyleColorModifier_DistanceFromObject *)m)->color_ramp;
			break;
		case LS_MODIFIER_MATERIAL:
			color_ramp = ((LineStyleColorModifier_Material *)m)->color_ramp;
			break;
		default:
			continue;
		}
		link = (LinkData *) MEM_callocN( sizeof(LinkData), "link to color ramp");
		link->data = color_ramp;
		BLI_addtail(listbase, link);
	}
}

/* XXX Do we want to keep that goto? Or use a boolean var? */
char *FRS_path_from_ID_to_color_ramp(FreestyleLineStyle *linestyle, ColorBand *color_ramp)
{
	LineStyleModifier *m;

	for (m = (LineStyleModifier *)linestyle->color_modifiers.first; m; m = m->next) {
		switch (m->type) {
		case LS_MODIFIER_ALONG_STROKE:
			if (color_ramp == ((LineStyleColorModifier_AlongStroke *)m)->color_ramp)
				goto found;
			break;
		case LS_MODIFIER_DISTANCE_FROM_CAMERA:
			if (color_ramp == ((LineStyleColorModifier_DistanceFromCamera *)m)->color_ramp)
				goto found;
			break;
		case LS_MODIFIER_DISTANCE_FROM_OBJECT:
			if (color_ramp == ((LineStyleColorModifier_DistanceFromObject *)m)->color_ramp)
				goto found;
			break;
		case LS_MODIFIER_MATERIAL:
			if (color_ramp == ((LineStyleColorModifier_Material *)m)->color_ramp)
				goto found;
			break;
		}
	}
	printf("FRS_path_from_ID_to_color_ramp: No color ramps correspond to the given pointer.\n");
	return NULL;

found:
	return BLI_sprintfN("color_modifiers[\"%s\"].color_ramp", m->name);
}

void FRS_unlink_linestyle_target_object(FreestyleLineStyle *linestyle, struct Object *ob)
{
	LineStyleModifier *m;

	for (m = (LineStyleModifier *)linestyle->color_modifiers.first; m; m = m->next) {
		if (m->type == LS_MODIFIER_DISTANCE_FROM_OBJECT) {
			if (((LineStyleColorModifier_DistanceFromObject *)m)->target == ob) {
				((LineStyleColorModifier_DistanceFromObject *)m)->target = NULL;
			}
		}
	}
	for (m = (LineStyleModifier *)linestyle->alpha_modifiers.first; m; m = m->next) {
		if (m->type == LS_MODIFIER_DISTANCE_FROM_OBJECT) {
			if (((LineStyleAlphaModifier_DistanceFromObject *)m)->target == ob) {
				((LineStyleAlphaModifier_DistanceFromObject *)m)->target = NULL;
			}
		}
	}
	for (m = (LineStyleModifier *)linestyle->thickness_modifiers.first; m; m = m->next) {
		if (m->type == LS_MODIFIER_DISTANCE_FROM_OBJECT) {
			if (((LineStyleThicknessModifier_DistanceFromObject *)m)->target == ob) {
				((LineStyleThicknessModifier_DistanceFromObject *)m)->target = NULL;
			}
		}
	}
}
