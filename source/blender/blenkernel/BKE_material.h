/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * General operations, lookup, etc. for materials.
 */

#ifndef BKE_MATERIAL_H
#define BKE_MATERIAL_H

#ifdef __cplusplus
extern "C" {
#endif

struct Material;
struct ID;
struct Object;

void free_material(struct Material *sc); 
void test_object_materials(struct ID *id);
void init_material(struct Material *ma);
struct Material *add_material(char *name);
struct Material *copy_material(struct Material *ma);
void make_local_material(struct Material *ma);

struct Material ***give_matarar(struct Object *ob);
short *give_totcolp(struct Object *ob);
struct Material *give_current_material(struct Object *ob, int act);
ID *material_from(struct Object *ob, int act);
void assign_material(struct Object *ob, struct Material *ma, int act);
void new_material_to_objectdata(struct Object *ob);

struct Material *get_active_matlayer(struct Material *);
void init_render_material(struct Material *);
void init_render_materials(void);
void end_render_material(struct Material *);
void end_render_materials(void);

void automatname(struct Material *);
void delete_material_index(void);            

#ifdef __cplusplus
}
#endif

#endif

