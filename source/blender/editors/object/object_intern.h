/**
 * $Id:
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef ED_OBJECT_INTERN_H
#define ED_OBJECT_INTERN_H

/* internal exports only */
#define CLEAR_OBJ_ROTATION 0
#define CLEAR_OBJ_LOCATION 1
#define CLEAR_OBJ_SCALE 2
#define CLEAR_OBJ_ORIGIN 3

/* object_edit.c */
void OBJECT_OT_toggle_editmode(wmOperatorType *ot);
void OBJECT_OT_make_parent(wmOperatorType *ot);
void OBJECT_OT_clear_parent(wmOperatorType *ot);
void OBJECT_OT_make_track(wmOperatorType *ot);
void OBJECT_OT_clear_track(wmOperatorType *ot);
void OBJECT_OT_de_select_all(wmOperatorType *ot);
void OBJECT_OT_select_invert(wmOperatorType *ot);
void OBJECT_OT_select_random(wmOperatorType *ot);
void OBJECT_OT_select_by_type(wmOperatorType *ot);
void OBJECT_OT_select_by_layer(wmOperatorType *ot);
void OBJECT_OT_clear_location(wmOperatorType *ot);
void OBJECT_OT_clear_rotation(wmOperatorType *ot);
void OBJECT_OT_clear_scale(wmOperatorType *ot);
void OBJECT_OT_clear_origin(wmOperatorType *ot);

#endif /* ED_OBJECT_INTERN_H */

