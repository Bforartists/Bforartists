/**
 * blenlib/BKE_texture.h (mar-2001 nzc)
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef BKE_TEXTURE_H
#define BKE_TEXTURE_H

#ifdef __cplusplus
extern "C" {
#endif

struct bNode;
struct Brush;
struct ColorBand;
struct EnvMap;
struct HaloRen;
struct Lamp;
struct LampRen;
struct Material;
struct MTex;
struct PluginTex;
struct PointDensity;
struct Tex;
struct TexMapping;
struct VoxelData;
struct World;

/*  in ColorBand struct */
#define MAXCOLORBAND 32


void free_texture(struct Tex *t); 
int test_dlerr(const char *name,  const char *symbol);
void open_plugin_tex(struct PluginTex *pit);
struct PluginTex *add_plugin_tex(char *str);
void free_plugin_tex(struct PluginTex *pit);

void init_colorband(struct ColorBand *coba, int rangetype);
struct ColorBand *add_colorband(int rangetype);
int do_colorband(struct ColorBand *coba, float in, float out[4]);
void colorband_table_RGBA(struct ColorBand *coba, float **array, int *size);
int vergcband(const void *a1, const void *a2);
struct CBData *colorband_element_add(struct ColorBand *coba, float position);
int colorband_element_remove(struct ColorBand *coba, int index);

void default_tex(struct Tex *tex);
struct Tex *add_texture(const char *name);
void tex_set_type(struct Tex *tex, int type);
void default_mtex(struct MTex *mtex);
struct MTex *add_mtex(void);
struct MTex *add_mtex_id(struct ID *id, int slot);
struct Tex *copy_texture(struct Tex *tex);
void make_local_texture(struct Tex *tex);
void autotexname(struct Tex *tex);

struct Tex *give_current_object_texture(struct Object *ob);
struct Tex *give_current_material_texture(struct Material *ma);
struct Tex *give_current_lamp_texture(struct Lamp *la);
struct Tex *give_current_world_texture(struct World *world);
struct Tex *give_current_brush_texture(struct Brush *br);

struct bNode *give_current_material_texture_node(struct Material *ma);

int			 give_active_mtex(struct ID *id, struct MTex ***mtex_ar, short *act);
void		 set_active_mtex(struct ID *id, short act);

void set_current_brush_texture(struct Brush *br, struct Tex *tex);
void set_current_world_texture(struct World *wo, struct Tex *tex);
void set_current_material_texture(struct Material *ma, struct Tex *tex);
void set_current_lamp_texture(struct Lamp *la, struct Tex *tex);

struct TexMapping *add_mapping(void);
void init_mapping(struct TexMapping *texmap);


void    BKE_free_envmapdata(struct EnvMap *env);
void    BKE_free_envmap(struct EnvMap *env);
struct EnvMap *BKE_add_envmap(void);
struct EnvMap *BKE_copy_envmap(struct EnvMap *env);

void    BKE_free_pointdensitydata(struct PointDensity *pd);
void    BKE_free_pointdensity(struct PointDensity *pd);
struct PointDensity *BKE_add_pointdensity(void);
struct PointDensity *BKE_copy_pointdensity(struct PointDensity *pd);

void BKE_free_voxeldatadata(struct VoxelData *vd);
void BKE_free_voxeldata(struct VoxelData *vd);
struct VoxelData *BKE_add_voxeldata(void);
struct VoxelData *BKE_copy_voxeldata(struct VoxelData *vd);

int     BKE_texture_dependsOnTime(const struct Tex *texture);

#ifdef __cplusplus
}
#endif

#endif

