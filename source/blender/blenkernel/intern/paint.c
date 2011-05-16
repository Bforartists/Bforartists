/*
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
 * along with this program; if not, write to the Free Software  Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 by Nicholas Bishop
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/paint.c
 *  \ingroup bke
 */



#include "DNA_object_types.h"
#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"
#include "DNA_brush_types.h"

#include "BLI_utildefines.h"


#include "BKE_brush.h"
#include "BKE_library.h"
#include "BKE_paint.h"

#include <stdlib.h>
#include <string.h>

const char PAINT_CURSOR_SCULPT[3] = {255, 100, 100};
const char PAINT_CURSOR_VERTEX_PAINT[3] = {255, 255, 255};
const char PAINT_CURSOR_WEIGHT_PAINT[3] = {200, 200, 255};
const char PAINT_CURSOR_TEXTURE_PAINT[3] = {255, 255, 255};

Paint *paint_get_active(Scene *sce)
{
	if(sce) {
		ToolSettings *ts = sce->toolsettings;
		
		if(sce->basact && sce->basact->object) {
			switch(sce->basact->object->mode) {
			case OB_MODE_SCULPT:
				return &ts->sculpt->paint;
			case OB_MODE_VERTEX_PAINT:
				return &ts->vpaint->paint;
			case OB_MODE_WEIGHT_PAINT:
				return &ts->wpaint->paint;
			case OB_MODE_TEXTURE_PAINT:
				return &ts->imapaint.paint;
			}
		}

		/* default to image paint */
		return &ts->imapaint.paint;
	}

	return NULL;
}

Brush *paint_brush(Paint *p)
{
	return p ? p->brush : NULL;
}

void paint_brush_set(Paint *p, Brush *br)
{
	if(p)
		p->brush= br;
}

int paint_facesel_test(Object *ob)
{
	return (ob && ob->type==OB_MESH && ob->data && (((Mesh *)ob->data)->editflag & ME_EDIT_PAINT_MASK) && (ob->mode & (OB_MODE_VERTEX_PAINT|OB_MODE_WEIGHT_PAINT|OB_MODE_TEXTURE_PAINT)));
}

void paint_init(Paint *p, const char col[3])
{
	Brush *brush;

	/* If there's no brush, create one */
	brush = paint_brush(p);
	if(brush == NULL)
		brush= add_brush("Brush");
	paint_brush_set(p, brush);

	memcpy(p->paint_cursor_col, col, 3);
	p->paint_cursor_col[3] = 128;

	p->flags |= PAINT_SHOW_BRUSH;
}

void free_paint(Paint *UNUSED(paint))
{
	/* nothing */
}

void copy_paint(Paint *src, Paint *tar)
{
	tar->brush= src->brush;
}
