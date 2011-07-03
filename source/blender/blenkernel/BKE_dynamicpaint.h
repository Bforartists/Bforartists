/**
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * Contributor(s): Miika H�m�l�inen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BKE_DYNAMIC_PAINT_H_
#define BKE_DYNAMIC_PAINT_H_

#include "DNA_dynamicpaint_types.h"

struct PaintEffectData;

/* Actual surface point	*/
typedef struct PaintSurfaceData {
	/* surface format data */
	void *format_data;
	/* surface type data */
	void *type_data;
	/* point neighbor data */
	struct PaintAdjData *adj_data;

	unsigned int total_points;
	short samples;

} PaintSurfaceData;

/* Paint type surface point	*/
typedef struct PaintPoint {

	/* Wet paint is handled at effect layer only
	*  and mixed to surface when drying */
	float e_color[3];
	float e_alpha;
	float wetness;
	short state;	/* -1 = doesn't exist (On UV mapped image
					*	    there can be points that doesn't exist on mesh surface)
					*  0 = empty or dry
					*  1 = wet paint
					*  2 = new paint */
	float color[3];
	float alpha;
} PaintPoint;

/* heigh field waves	*/
typedef struct PaintWavePoint {		

	float height;
	float velocity;
	short state; /* 0 = neutral
				 *  1 = obstacle
				 *  2 = reflect only */
	float foam;

} PaintWavePoint;

struct DerivedMesh *dynamicPaint_Modifier_do(struct DynamicPaintModifierData *pmd, struct Scene *scene, struct Object *ob, struct DerivedMesh *dm);
void dynamicPaint_Modifier_free (struct DynamicPaintModifierData *pmd);
void dynamicPaint_Modifier_createType(struct DynamicPaintModifierData *pmd);
void dynamicPaint_Modifier_copy(struct DynamicPaintModifierData *pmd, struct DynamicPaintModifierData *tsmd);

void dynamicPaint_cacheUpdateFrames(struct DynamicPaintSurface *surface);
void dynamicPaint_clearSurface(DynamicPaintSurface *surface);
int  dynamicPaint_resetSurface(struct DynamicPaintSurface *surface);
int  dynamicPaint_surfaceHasColorPreview(DynamicPaintSurface *surface);
void dynamicPaintSurface_updateType(struct DynamicPaintSurface *surface);
void dynamicPaintSurface_setUniqueName(DynamicPaintSurface *surface, char *basename);

#endif /* BKE_DYNAMIC_PAINT_H_ */
