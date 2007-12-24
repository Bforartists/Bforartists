/*
 * $Id: BPY_extern.h 12334 2007-10-21 23:00:29Z aligorith $
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
 * The Original Code was in: source/blender/bpython/include/BPY_extern.h
 *
 * Contributor(s): Michel Selten, Willian P. Germano, Chris Keith
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef BPY_EXTERN_H
#define BPY_EXTERN_H

extern char bprogname[];	/* holds a copy of argv[0], from creator.c */

struct Text; /* defined in DNA_text_types.h */
struct ID; /* DNA_ID.h */
struct Object; /* DNA_object_types.h */
struct IpoDriver; /* DNA_curve_types.h */
struct ScriptLink; /* DNA_scriptlink_types.h */
struct ListBase; /* DNA_listBase.h */
struct SpaceText; /* DNA_space_types.h */
struct SpaceScript; /* DNA_space_types.h */
struct Script; /* BPI_script.h */
struct ScrArea; /* DNA_screen_types.h */
struct bScreen; /* DNA_screen_types.h */
struct bConstraint; /* DNA_constraint_types.h */
struct bPythonConstraint; /* DNA_constraint_types.h */
struct bConstraintOb; /* DNA_constraint_types.h */
struct bConstraintTarget; /* DNA_constraint_types.h*/
#ifdef __cplusplus
extern "C" {
#endif

	/*These two next functions are important for making sure the Draw module
	  works correctly.  Before calling any gui callback using the Draw module,
	  the following code must be executed:
	  
		if (some_drawspace_pylist) {
			BPy_Set_DrawButtonsList(some_drawspace_pylist->but_refs);
			BPy_Free_DrawButtonsList();
		}
		some_drawspace_pylist = PyList_New(0);
		BPy_Set_DrawButtonsList(some_drawspace_pylist);

      Also, BPy_Free_DrawButtonsList() must be called as necassary when a drawspace
      with python callbacks is destroyed.
      
      This is necassary to avoid blender buttons storing invalid pointers to freed
      python data.*/
	void BPy_Set_DrawButtonsList(void *list);
	void BPy_Free_DrawButtonsList(void);
	
	void BPY_pyconstraint_eval(struct bPythonConstraint *con, struct bConstraintOb *cob, struct ListBase *targets);
	void BPY_pyconstraint_settings(void *arg1, void *arg2);
	void BPY_pyconstraint_target(struct bPythonConstraint *con, struct bConstraintTarget *ct);
	void BPY_pyconstraint_update(struct Object *owner, struct bConstraint *con);
	int BPY_is_pyconstraint(struct Text *text);
	
	void BPY_start_python( int argc, char **argv );
	void BPY_end_python( void );
	void BPY_post_start_python( void );
	void init_syspath( int first_time );
	void syspath_append( char *dir );

	int BPY_Err_getLinenumber( void );
	const char *BPY_Err_getFilename( void );

	int BPY_txt_do_python_Text( struct Text *text );
	int BPY_menu_do_python( short menutype, int event );
	void BPY_run_python_script( char *filename );
	void BPY_free_compiled_text( struct Text *text );

	void BPY_clear_bad_scriptlinks( struct Text *byebye );
	int BPY_has_onload_script( void );
	void BPY_do_all_scripts( short event );
	int BPY_check_all_scriptlinks( struct Text *text );
	void BPY_do_pyscript( struct ID *id, short event );
	void BPY_free_scriptlink( struct ScriptLink *slink );
	void BPY_copy_scriptlink( struct ScriptLink *scriptlink );

	int BPY_is_spacehandler(struct Text *text, char spacetype);
	int BPY_del_spacehandler(struct Text *text, struct ScrArea *sa);
	int BPY_add_spacehandler(struct Text *txt, struct ScrArea *sa,char spacetype);
	int BPY_has_spacehandler(struct Text *text, struct ScrArea *sa);
	void BPY_screen_free_spacehandlers(struct bScreen *sc);
	int BPY_do_spacehandlers(struct ScrArea *sa, unsigned short event,
		unsigned short space_event);

	void BPY_pydriver_update(void);
	float BPY_pydriver_eval(struct IpoDriver *driver);
	struct Object **BPY_pydriver_get_objects(struct IpoDriver *driver);

	int BPY_button_eval(char *expr, double *value);

/* format importer hook */
	int BPY_call_importloader( char *name );

	void BPY_spacescript_do_pywin_draw( struct SpaceScript *sc );
	void BPY_spacescript_do_pywin_event( struct SpaceScript *sc,
					     unsigned short event, short val, char ascii );
	void BPY_clear_script( struct Script *script );
	void BPY_free_finished_script( struct Script *script );

/* void BPY_Err_Handle(struct Text *text); */
/* void BPY_clear_bad_scriptlink(struct ID *id, struct Text *byebye); */
/* void BPY_clear_bad_scriptlist(struct ListBase *, struct Text *byebye); */
/* int BPY_spacetext_is_pywin(struct SpaceText *st); */

#ifdef __cplusplus
}				/* extern "C" */
#endif

#endif  /* BPY_EXTERN_H */
