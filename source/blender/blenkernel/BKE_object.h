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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BKE_OBJECT_H
#define BKE_OBJECT_H

/** \file BKE_object.h
 *  \ingroup bke
 *  \brief General operations, lookup, etc. for blender objects.
 */
#ifdef __cplusplus
extern "C" {
#endif

struct Base;
struct Scene;
struct Object;
struct Camera;
struct BoundBox;
struct View3D;
struct SoftBody;
struct BulletSoftBody;
struct Group;
struct bAction;
struct RenderData;
struct rctf;

void clear_workob(struct Object *workob);
void what_does_parent(struct Scene *scene, struct Object *ob, struct Object *workob);

void copy_baseflags(struct Scene *scene);
void copy_objectflags(struct Scene *scene);
struct SoftBody *copy_softbody(struct SoftBody *sb);
struct BulletSoftBody *copy_bulletsoftbody(struct BulletSoftBody *sb);
void copy_object_particlesystems(struct Object *obn, struct Object *ob);
void copy_object_softbody(struct Object *obn, struct Object *ob);
void object_free_particlesystems(struct Object *ob);
void object_free_softbody(struct Object *ob);
void object_free_bulletsoftbody(struct Object *ob);
void update_base_layer(struct Scene *scene, struct Object *ob);

void free_object(struct Object *ob);
void object_free_display(struct Object *ob);

void object_link_modifiers(struct Object *ob, struct Object *from);
void object_free_modifiers(struct Object *ob);

void object_make_proxy(struct Object *ob, struct Object *target, struct Object *gob);
void object_copy_proxy_drivers(struct Object *ob, struct Object *target);

void unlink_object(struct Object *ob);
int exist_object(struct Object *obtest);
void *add_camera(const char *name);
struct Camera *copy_camera(struct Camera *cam);
void make_local_camera(struct Camera *cam);
float dof_camera(struct Object *ob);
	
void *add_lamp(const char *name);
struct Lamp *copy_lamp(struct Lamp *la);
struct Lamp *localize_lamp(struct Lamp *la);
void make_local_lamp(struct Lamp *la);
void free_camera(struct Camera *ca);
void free_lamp(struct Lamp *la);

struct Object *add_only_object(int type, const char *name);
struct Object *add_object(struct Scene *scene, int type);

struct Object *copy_object(struct Object *ob);
void make_local_object(struct Object *ob);
int object_is_libdata(struct Object *ob);
int object_data_is_libdata(struct Object *ob);
void set_mblur_offs(float blur);
void set_field_offs(float field);
void disable_speed_curve(int val);

float bsystem_time(struct Scene *scene, struct Object *ob, float cfra, float ofs);
void object_scale_to_mat3(struct Object *ob, float mat[][3]);
void object_rot_to_mat3(struct Object *ob, float mat[][3]);
void object_mat3_to_rot(struct Object *ob, float mat[][3], short use_compat);
void object_to_mat3(struct Object *ob, float mat[][3]);
void object_to_mat4(struct Object *ob, float mat[][4]);
void object_apply_mat4(struct Object *ob, float mat[][4], const short use_compat, const short use_parent);

void set_no_parent_ipo(int val);
struct Object *object_pose_armature_get(struct Object *ob);

void where_is_object_time(struct Scene *scene, struct Object *ob, float ctime);
void where_is_object(struct Scene *scene, struct Object *ob);
void where_is_object_simul(struct Scene *scene, struct Object *ob);

struct BoundBox *unit_boundbox(void);
void boundbox_set_from_min_max(struct BoundBox *bb, float min[3], float max[3]);
struct BoundBox *object_get_boundbox(struct Object *ob);
void object_get_dimensions(struct Object *ob, float *value);
void object_set_dimensions(struct Object *ob, const float *value);
void object_boundbox_flag(struct Object *ob, int flag, int set);
void minmax_object(struct Object *ob, float *min, float *max);
int minmax_object_duplis(struct Scene *scene, struct Object *ob, float *min, float *max);
void solve_tracking (struct Object *ob, float targetmat[][4]);
int ray_hit_boundbox(struct BoundBox *bb, float ray_start[3], float ray_normal[3]);

void *object_tfm_backup(struct Object *ob);
void object_tfm_restore(struct Object *ob, void *obtfm_pt);

void object_handle_update(struct Scene *scene, struct Object *ob);
void object_sculpt_modifiers_changed(struct Object *ob);

float give_timeoffset(struct Object *ob);
int give_obdata_texspace(struct Object *ob, short **texflag, float **loc, float **size, float **rot);

int object_insert_ptcache(struct Object *ob);
// void object_delete_ptcache(struct Object *ob, int index);
struct KeyBlock *object_insert_shape_key(struct Scene *scene, struct Object *ob, const char *name, int from_mix);

int object_is_modified(struct Scene *scene, struct Object *ob);

void object_camera_mode(struct RenderData *rd, struct Object *camera);
void object_camera_intrinsics(struct Object *camera, struct Camera **cam_r, short *is_ortho, float *shiftx, float *shifty,
			float *clipsta, float *clipend, float *lens, float *sensor_x, float *sensor_y, short *sensor_fit);
void object_camera_matrix(
		struct RenderData *rd, struct Object *camera, int winx, int winy, short field_second,
		float winmat[][4], struct rctf *viewplane, float *clipsta, float *clipend, float *lens,
		float *sensor_x, float *sensor_y, short *sensor_fit, float *ycor,
		float *viewdx, float *viewdy);

void camera_view_frame_ex(struct Scene *scene, struct Camera *camera, float drawsize, const short do_clip, const float scale[3],
                          float r_asp[2], float r_shift[2], float *r_drawsize, float r_vec[4][3]);

void camera_view_frame(struct Scene *scene, struct Camera *camera, float r_vec[4][3]);

void object_relink(struct Object *ob);

#ifdef __cplusplus
}
#endif

#endif
