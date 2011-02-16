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
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code was in: source/blender/bpython/include/BPY_extern.h
 *
 * Contributor(s): Michel Selten, Willian P. Germano, Chris Keith
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BPY_EXTERN_H
#define BPY_EXTERN_H

extern char bprogname[];	/* holds a copy of argv[0], from creator.c */

struct Text; /* defined in DNA_text_types.h */
struct ID; /* DNA_ID.h */
struct Object; /* DNA_object_types.h */
struct ChannelDriver; /* DNA_anim_types.h */
struct ListBase; /* DNA_listBase.h */
struct SpaceText; /* DNA_space_types.h */
struct ScrArea; /* DNA_screen_types.h */
struct bScreen; /* DNA_screen_types.h */
struct bConstraint; /* DNA_constraint_types.h */
struct bPythonConstraint; /* DNA_constraint_types.h */
struct bConstraintOb; /* DNA_constraint_types.h */
struct bConstraintTarget; /* DNA_constraint_types.h*/
struct BPyMenu;
struct bContext;
struct bContextDataResult;
struct ReportList;

#ifdef __cplusplus
extern "C" {
#endif

void BPY_pyconstraint_exec(struct bPythonConstraint *con, struct bConstraintOb *cob, struct ListBase *targets);
//	void BPY_pyconstraint_settings(void *arg1, void *arg2);
void BPY_pyconstraint_target(struct bPythonConstraint *con, struct bConstraintTarget *ct);
void BPY_pyconstraint_update(struct Object *owner, struct bConstraint *con);
int BPY_is_pyconstraint(struct Text *text);
//	void BPY_free_pyconstraint_links(struct Text *text);
//
void BPY_python_start( int argc, char **argv );
void BPY_python_end( void );
//	void init_syspath( int first_time );
//	void syspath_append( char *dir );
//	void BPY_rebuild_syspath( void );
//	int BPY_path_update( void );
//
//	int BPY_Err_getLinenumber( void );
//	const char *BPY_Err_getFilename( void );

/* 2.5 UI Scripts */
int		BPY_filepath_exec(struct bContext *C, const char *filepath, struct ReportList *reports);
int		BPY_text_exec(struct bContext *C, struct Text *text, struct ReportList *reports);
void	BPY_text_free_code(struct Text *text);
void	BPY_modules_update(struct bContext *C); // XXX - annoying, need this for pointers that get out of date
void	BPY_modules_load_user(struct bContext *C);

void	BPY_driver_reset(void);
float	BPY_driver_exec(struct ChannelDriver *driver);

int		BPY_button_exec(struct bContext *C, const char *expr, double *value);
int		BPY_string_exec(struct bContext *C, const char *expr);

void	BPY_DECREF(void *pyob_ptr);	/* Py_DECREF() */
int		BPY_context_member_get(struct bContext *C, const char *member, struct bContextDataResult *result);
void	BPY_context_set(struct bContext *C);

#ifdef __cplusplus
}				/* extern "C" */
#endif

#endif  /* BPY_EXTERN_H */
