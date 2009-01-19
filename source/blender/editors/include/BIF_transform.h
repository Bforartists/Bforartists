/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BIF_TRANSFORM_H
#define BIF_TRANSFORM_H

/* ******************* Registration Function ********************** */

struct wmWindowManager;
struct ListBase;
struct wmEvent;
struct bContext;
struct Object;

void transform_keymap_for_space(struct wmWindowManager *wm, struct ListBase *keymap, int spaceid);
void transform_operatortypes(void);

/* ******************** Macros & Prototypes *********************** */

/* MODE AND NUMINPUT FLAGS */
enum {
	TFM_INIT = -1,
	TFM_DUMMY,
	TFM_TRANSLATION,
	TFM_ROTATION,
	TFM_RESIZE,
	TFM_TOSPHERE,
	TFM_SHEAR,
	TFM_WARP,
	TFM_SHRINKFATTEN,
	TFM_TILT,
	TFM_LAMP_ENERGY,
	TFM_TRACKBALL,
	TFM_PUSHPULL,
	TFM_CREASE,
	TFM_MIRROR,
	TFM_BONESIZE,
	TFM_BONE_ENVELOPE,
	TFM_CURVE_SHRINKFATTEN,
	TFM_BONE_ROLL,
	TFM_TIME_TRANSLATE,
	TFM_TIME_SLIDE,
	TFM_TIME_SCALE,
	TFM_TIME_EXTEND,
	TFM_BAKE_TIME,
	TFM_BEVEL,
	TFM_BWEIGHT,
	TFM_ALIGN
} TfmMode;

/* TRANSFORM CONTEXTS */
#define CTX_NONE			0
#define CTX_TEXTURE			1
#define CTX_EDGE			2
#define CTX_NO_PET			4
#define CTX_TWEAK			8
#define CTX_NO_MIRROR		16
#define CTX_AUTOCONFIRM		32
#define CTX_BMESH			64
#define CTX_NDOF			128

/* Standalone call to get the transformation center corresponding to the current situation
 * returns 1 if successful, 0 otherwise (usually means there's no selection)
 * (if 0 is returns, *vec is unmodified) 
 * */
int calculateTransformCenter(struct bContext *C, struct wmEvent *event, int centerMode, float *vec);

struct TransInfo;
struct ScrArea;
struct Base;
struct Scene;

void BIF_setSingleAxisConstraint(float vec[3], char *text);
void BIF_setDualAxisConstraint(float vec1[3], float vec2[3], char *text);
void BIF_setLocalAxisConstraint(char axis, char *text);
void BIF_setLocalLockConstraint(char axis, char *text);

int BIF_snappingSupported(struct Object *obedit);

struct TransformOrientation;
struct bContext;

void BIF_clearTransformOrientation(struct bContext *C);
void BIF_removeTransformOrientation(struct bContext *C, struct TransformOrientation *ts);
void BIF_manageTransformOrientation(struct bContext *C, int confirm, int set);
int BIF_menuselectTransformOrientation(void);
void BIF_selectTransformOrientation(struct bContext *C, struct TransformOrientation *ts);
void BIF_selectTransformOrientationValue(struct bContext *C, int orientation);

char * BIF_menustringTransformOrientation(const struct bContext *C, char *title); /* the returned value was allocated and needs to be freed after use */
int BIF_countTransformOrientation(const struct bContext *C);

void BIF_getPropCenter(float *center);

void BIF_TransformSetUndo(char *str);

void BIF_selectOrientation(void);

/* view3d manipulators */
void initManipulator(int mode);
void ManipulatorTransform();

//int BIF_do_manipulator(struct ScrArea *sa);
//void BIF_draw_manipulator(struct ScrArea *sa);

#endif

