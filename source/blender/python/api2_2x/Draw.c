/* 
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Willian P. Germano, Campbell Barton, Ken Hughes
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

/* This file is the Blender.Draw part of opy_draw.c, from the old
 * bpython/intern dir, with minor changes to adapt it to the new Python
 * implementation.	Non-trivial original comments are marked with an
 * @ symbol at their beginning. */

#include "Draw.h" /*This must come first*/

#include "BLI_blenlib.h"
#include "MEM_guardedalloc.h"
#include "BMF_Api.h"
#include "DNA_screen_types.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_object.h"
#include "BKE_main.h"
#include "BIF_gl.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_interface.h"
#include "BIF_toolbox.h"
#include "BPI_script.h"		/* script struct */
#include "Image.h"              /* for accessing Blender.Image objects */
#include "IMB_imbuf_types.h"    /* for the IB_rect define */
#include "interface.h"
#include "mydevice.h"		/*@ for all the event constants */
#include "gen_utils.h"
#include "Window.h"

/* these delimit the free range for button events */
#define EXPP_BUTTON_EVENTS_OFFSET 1001
#define EXPP_BUTTON_EVENTS_MIN 0
#define EXPP_BUTTON_EVENTS_MAX 15382 /* 16384 - 1 - OFFSET */

/* pointer to main dictionary defined in Blender.c */
extern PyObject *g_blenderdict;

/*@ hack to flag that window redraw has happened inside slider callback: */
int EXPP_disable_force_draw = 0;

/* forward declarations for internal functions */
static void Button_dealloc( PyObject * self );
static PyObject *Button_getattr( PyObject * self, char *name );
static PyObject *Button_repr( PyObject * self );
static int Button_setattr( PyObject * self, char *name, PyObject * v );

static Button *newbutton( void );

/* GUI interface routines */

static void exit_pydraw( SpaceScript * sc, short error );
static void exec_callback( SpaceScript * sc, PyObject * callback,
			   PyObject * args );
static void spacescript_do_pywin_buttons( SpaceScript * sc,
					  unsigned short event );

static PyObject *Method_Exit( PyObject * self, PyObject * args );
static PyObject *Method_Register( PyObject * self, PyObject * args );
static PyObject *Method_Redraw( PyObject * self, PyObject * args );
static PyObject *Method_Draw( PyObject * self, PyObject * args );
static PyObject *Method_Create( PyObject * self, PyObject * args );

static PyObject *Method_Button( PyObject * self, PyObject * args );
static PyObject *Method_Menu( PyObject * self, PyObject * args );
static PyObject *Method_Toggle( PyObject * self, PyObject * args );
static PyObject *Method_Slider( PyObject * self, PyObject * args );
static PyObject *Method_Scrollbar( PyObject * self, PyObject * args );
static PyObject *Method_Number( PyObject * self, PyObject * args );
static PyObject *Method_String( PyObject * self, PyObject * args );
static PyObject *Method_GetStringWidth( PyObject * self, PyObject * args );
static PyObject *Method_Text( PyObject * self, PyObject * args );
static PyObject *Method_PupMenu( PyObject * self, PyObject * args );
/* next three by Campbell: */
static PyObject *Method_PupIntInput( PyObject * self, PyObject * args );
static PyObject *Method_PupFloatInput( PyObject * self, PyObject * args );
static PyObject *Method_PupStrInput( PyObject * self, PyObject * args );
/* next by Jonathan Merritt (lancelet): */
static PyObject *Method_Image( PyObject * self, PyObject * args);

static uiBlock *Get_uiBlock( void );
static void py_slider_update( void *butv, void *data2_unused );

static char Draw_doc[] = "The Blender.Draw submodule";

static char Method_Register_doc[] =
	"(draw, event, button) - Register callbacks for windowing\n\n\
(draw) A function to draw the screen, taking no arguments\n\
(event) A function to handle events, taking 2 arguments (evt, val)\n\
	(evt) The event number\n\
	(val) The value modifier (for key and mouse press/release)\n\
(button) A function to handle button events, taking 1 argument (evt)\n\
	(evt) The button number\n\n\
A None object can be passed if a callback is unused.";


static char Method_Redraw_doc[] = "([after]) - Queue a redraw event\n\n\
[after=0] Determines whether the redraw is processed before\n\
or after other input events.\n\n\
Redraw events are buffered so that regardless of how many events\n\
are queued the window only receives one redraw event.";

static char Method_Draw_doc[] = "() - Force an immediate redraw\n\n\
Forced redraws are not buffered, in other words the window is redrawn\n\
exactly once for everytime this function is called.";


static char Method_Create_doc[] =
	"(value) - Create a default Button object\n\n\
 (value) - The value to store in the button\n\n\
 Valid values are ints, floats, and strings";

static char Method_Button_doc[] =
	"(name, event, x, y, width, height, [tooltip]) - Create a new Button \
(push) button\n\n\
(name) A string to display on the button\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
[tooltip=] The button's tooltip\n\n\
This function can be called as Button() or PushButton().";

static char Method_Menu_doc[] =
	"(name, event, x, y, width, height, default, [tooltip]) - Create a new Menu \
button\n\n\
(name) A string to display on the button\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
(default) The number of the option to be selected by default\n\
[tooltip=" "] The button's tooltip\n\n\
The menu options are specified through the name of the\n\
button. Options are followed by a format code and separated\n\
by the '|' (pipe) character.\n\
Valid format codes are\n\
	%t - The option should be used as the title\n\
	%xN - The option should set the integer N in the button value.";

static char Method_Toggle_doc[] =
	"(name, event, x, y, width, height, default, [tooltip]) - Create a new Toggle \
button\n\n\
(name) A string to display on the button\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
(default) An integer (0 or 1) specifying the default state\n\
[tooltip=] The button's tooltip";


static char Method_Slider_doc[] =
	"(name, event, x, y, width, height, initial, min, max, [update, tooltip]) - \
Create a new Slider button\n\n\
(name) A string to display on the button\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
(initial, min, max) Three values (int or float) specifying the initial \
				and limit values.\n\
[update=1] A value controlling whether the slider will emit events as it \
is edited.\n\
	A non-zero value (default) enables the events. A zero value supresses them.\n\
[tooltip=] The button's tooltip";


static char Method_Scrollbar_doc[] =
	"(event, x, y, width, height, initial, min, max, [update, tooltip]) - Create a \
new Scrollbar\n\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
(initial, min, max) Three values (int or float) specifying the initial and limit values.\n\
[update=1] A value controlling whether the slider will emit events as it is edited.\n\
	A non-zero value (default) enables the events. A zero value supresses them.\n\
[tooltip=] The button's tooltip";

static char Method_Number_doc[] =
	"(name, event, x, y, width, height, initial, min, max, [tooltip]) - Create a \
new Number button\n\n\
(name) A string to display on the button\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
(initial, min, max) Three values (int or float) specifying the initial and \
limit values.\n\
[tooltip=] The button's tooltip";

static char Method_String_doc[] =
	"(name, event, x, y, width, height, initial, length, [tooltip]) - Create a \
new String button\n\n\
(name) A string to display on the button\n\
(event) The event number to pass to the button event function when activated\n\
(x, y) The lower left coordinate of the button\n\
(width, height) The button width and height\n\
(initial) The string to display initially\n\
(length) The maximum input length\n\
[tooltip=] The button's tooltip";

static char Method_GetStringWidth_doc[] =
	"(text, font = 'normal') - Return the width in pixels of the given string\n\
(font) The font size: 'normal' (default), 'small' or 'tiny'.";

static char Method_Text_doc[] =
	"(text, font = 'normal') - Draw text onscreen\n\n\
(text) The text to draw\n\
(font) The font size: 'normal' (default), 'small' or 'tiny'.\n\n\
This function returns the width of the drawn string.";

static char Method_PupMenu_doc[] =
	"(string, maxrow = None) - Display a pop-up menu at the screen.\n\
The contents of the pop-up are specified through the 'string' argument,\n\
like with Draw.Menu.\n\
'maxrow' is an optional int to control how many rows the pop-up should have.\n\
Options are followed by a format code and separated\n\
by the '|' (pipe) character.\n\
Valid format codes are\n\
	%t - The option should be used as the title\n\
	%xN - The option should set the integer N in the button value.\n\n\
Ex: Draw.PupMenu('OK?%t|QUIT BLENDER') # should be familiar ...";

static char Method_PupIntInput_doc[] =
	"(text, default, min, max) - Display an int pop-up input.\n\
(text) - text string to display on the button;\n\
(default, min, max) - the default, min and max int values for the button;\n\
Return the user input value or None on user exit";

static char Method_PupFloatInput_doc[] =
	"(text, default, min, max, clickStep, floatLen) - Display a float pop-up input.\n\
(text) - text string to display on the button;\n\
(default, min, max) - the default, min and max float values for the button;\n\
(clickStep) - float increment/decrement for each click on the button arrows;\n\
(floatLen) - an integer defining the precision (number of decimal places) of \n\
the float value show.\n\
Return the user input value or None on user exit";

static char Method_Image_doc[] =
	"(image, x, y, zoomx = 1.0, zoomy = 1.0, [clipx, clipy, clipw, cliph])) \n\
    - Draw an image.\n\
(image) - Blender.Image to draw.\n\
(x, y) - floats specifying the location of the image.\n\
(zoomx, zoomy) - float zoom factors in horizontal and vertical directions.\n\
(clipx, clipy, clipw, cliph) - integers specifying a clipping rectangle within the original image.";

static char Method_PupStrInput_doc[] =
	"(text, default, max = 20) - Display a float pop-up input.\n\
(text) - text string to display on the button;\n\
(default) - the initial string to display (truncated to 'max' chars);\n\
(max = 20) - The maximum number of chars the user can input;\n\
Return the user input value or None on user exit";

static char Method_Exit_doc[] = "() - Exit the windowing interface";

/*
* here we engage in some macro trickery to define the PyMethodDef table
*/

#define _MethodDef(func, prefix) \
	{#func, prefix##_##func, METH_VARARGS, prefix##_##func##_doc}

/* So that _MethodDef(delete, Scene) expands to:
 * {"delete", Scene_delete, METH_VARARGS, Scene_delete_doc} */

#undef MethodDef
#define MethodDef(func) _MethodDef(func, Method)

static struct PyMethodDef Draw_methods[] = {
	MethodDef( Create ),
	MethodDef( Button ),
	MethodDef( Toggle ),
	MethodDef( Menu ),
	MethodDef( Slider ),
	MethodDef( Scrollbar ),
	MethodDef( Number ),
	MethodDef( String ),
	MethodDef( GetStringWidth ),
	MethodDef( Text ),
	MethodDef( PupMenu ),
	MethodDef( PupIntInput ),
	MethodDef( PupFloatInput ),
	MethodDef( PupStrInput ),
	MethodDef( Image ),
	MethodDef( Exit ),
	MethodDef( Redraw ),
	MethodDef( Draw ),
	MethodDef( Register ),
	{"PushButton", Method_Button, METH_VARARGS, Method_Button_doc},
	{NULL, NULL, 0, NULL}
};

PyTypeObject Button_Type = {
	PyObject_HEAD_INIT( NULL ) 0,	/*ob_size */
	"Button",		/*tp_name */
	sizeof( Button ),	/*tp_basicsize */
	0,			/*tp_itemsize */
	( destructor ) Button_dealloc,	/*tp_dealloc */
	( printfunc ) 0,	/*tp_print */
	( getattrfunc ) Button_getattr,	/*tp_getattr */
	( setattrfunc ) Button_setattr,	/*tp_setattr */
	( cmpfunc ) 0,		/*tp_cmp */
	( reprfunc ) Button_repr,	/*tp_repr */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
};

static void Button_dealloc( PyObject * self )
{
	Button *but = ( Button * ) self;

	if( but->type == 3 ) {
		if( but->val.asstr )
			MEM_freeN( but->val.asstr );
	}

	PyObject_DEL( self );
}

static PyObject *Button_getattr( PyObject * self, char *name )
{
	Button *but = ( Button * ) self;

	if( strcmp( name, "val" ) == 0 ) {
		if( but->type == 1 )
			return Py_BuildValue( "i", but->val.asint );
		else if( but->type == 2 )
			return Py_BuildValue( "f", but->val.asfloat );
		else if( but->type == 3 )
			return Py_BuildValue( "s", but->val.asstr );
	}

	PyErr_SetString( PyExc_AttributeError, name );
	return NULL;
}

static int Button_setattr( PyObject * self, char *name, PyObject * v )
{
	Button *but = ( Button * ) self;

	if( strcmp( name, "val" ) == 0 ) {
		if( but->type == 1 )
			PyArg_Parse( v, "i", &but->val.asint );
		else if( but->type == 2 )
			PyArg_Parse( v, "f", &but->val.asfloat );
		else if( but->type == 3 ) {
			char *newstr;
			PyArg_Parse( v, "s", &newstr );

			/* if the length of the new string is the same as */
			/* the old one, just copy, else delete and realloc. */
			if( but->slen == strlen( newstr ) ) {
				BLI_strncpy( but->val.asstr, newstr,
					     but->slen + 1 );
			} else {
				MEM_freeN( but->val.asstr );
				but->slen = strlen( newstr );
				but->val.asstr =
					MEM_mallocN( but->slen + 1,
						     "button setattr" );
				BLI_strncpy( but->val.asstr, newstr,
					     but->slen + 1 );
			}
		}
	} else {
		PyErr_SetString( PyExc_AttributeError, name );
		return -1;
	}

	return 0;
}

static PyObject *Button_repr( PyObject * self )
{
	return PyObject_Repr( Button_getattr( self, "val" ) );
}

static Button *newbutton( void )
{
	Button *but = ( Button * ) PyObject_NEW( Button, &Button_Type );

	return but;
}

/* GUI interface routines */

static void exit_pydraw( SpaceScript * sc, short err )
{
	Script *script = NULL;

	if( !sc || !sc->script )
		return;

	script = sc->script;

	if( err ) {
		PyErr_Print(  );
		script->flags = 0;	/* mark script struct for deletion */
		error( "Python script error: check console" );
		scrarea_queue_redraw( sc->area );
	}

	Py_XDECREF( ( PyObject * ) script->py_draw );
	Py_XDECREF( ( PyObject * ) script->py_event );
	Py_XDECREF( ( PyObject * ) script->py_button );

	script->py_draw = script->py_event = script->py_button = NULL;
}

static void exec_callback( SpaceScript * sc, PyObject * callback,
			   PyObject * args )
{
	PyObject *result = PyObject_CallObject( callback, args );

	if( result == NULL && sc->script ) {	/* errors in the script */

		if( sc->script->lastspace == SPACE_TEXT ) {	/*if it can be an ALT+P script */
			Text *text = G.main->text.first;

			while( text ) {	/* find it and free its compiled code */

				if( !strcmp
				    ( text->id.name + 2,
				      sc->script->id.name + 2 ) ) {
					BPY_free_compiled_text( text );
					break;
				}

				text = text->id.next;
			}
		}
		exit_pydraw( sc, 1 );
	}

	Py_XDECREF( result );
	Py_DECREF( args );
}

/* BPY_spacescript_do_pywin_draw, the static spacescript_do_pywin_buttons and
 * BPY_spacescript_do_pywin_event are the three functions responsible for
 * calling the draw, buttons and event callbacks registered with Draw.Register
 * (see Method_Register below).  They are called (only the two BPY_ ones)
 * from blender/src/drawscript.c */

void BPY_spacescript_do_pywin_draw( SpaceScript * sc )
{
	uiBlock *block;
	char butblock[20];
	Script *script = sc->script;

	sprintf( butblock, "win %d", curarea->win );
	block = uiNewBlock( &curarea->uiblocks, butblock, UI_EMBOSSX,
			    UI_HELV, curarea->win );

	if( script->py_draw ) {
		glPushAttrib( GL_ALL_ATTRIB_BITS );
		exec_callback( sc, script->py_draw, Py_BuildValue( "()" ) );
		glPopAttrib(  );
	} else {
		glClearColor( 0.4375, 0.4375, 0.4375, 0.0 );
		glClear( GL_COLOR_BUFFER_BIT );
	}

	uiDrawBlock( block );

	curarea->win_swap = WIN_BACK_OK;
}

static void spacescript_do_pywin_buttons( SpaceScript * sc,
					  unsigned short event )
{
	if( sc->script->py_button )
		exec_callback( sc, sc->script->py_button,
			       Py_BuildValue( "(i)", event ) );
}

void BPY_spacescript_do_pywin_event( SpaceScript * sc, unsigned short event,
	short val, char ascii )
{
	if( event == QKEY && G.qual & ( LR_ALTKEY | LR_CTRLKEY ) ) {
		/* finish script: user pressed ALT+Q or CONTROL+Q */
		Script *script = sc->script;

		exit_pydraw( sc, 0 );

		script->flags &= ~SCRIPT_GUI;	/* we're done with this script */

		return;
	}

	if (val) {

		if (uiDoBlocks( &curarea->uiblocks, event ) != UI_NOTHING) event = 0;

		if (event == UI_BUT_EVENT) {
			/* check that event is in free range for script button events;
			 * read the comment before check_button_event() below to understand */
			if (val >= EXPP_BUTTON_EVENTS_OFFSET && val < 0x4000)
				spacescript_do_pywin_buttons(sc, val - EXPP_BUTTON_EVENTS_OFFSET);
			return;
		}
	}

	/* We use the "event" main module var, used by scriptlinks, to pass the ascii
	 * value to event callbacks (gui/event/button callbacks are not allowed
	 * inside scriptlinks, so this is ok) */
	if( sc->script->py_event ) {
		int pass_ascii = 0;
		if (ascii > 31 && ascii != 127) {
			pass_ascii = 1;
			PyDict_SetItemString(g_blenderdict, "event", PyInt_FromLong((long)ascii));
		}
		exec_callback( sc, sc->script->py_event,
			Py_BuildValue( "(ii)", event, val ) );
		if (pass_ascii)
			PyDict_SetItemString(g_blenderdict, "event", PyString_FromString(""));
	}
}

static PyObject *Method_Exit( PyObject * self, PyObject * args )
{
	SpaceScript *sc;
	Script *script;

	/* if users call Draw.Exit when we are already out of the SPACE_SCRIPT, we
	 * simply return, for compatibility */
	if( curarea->spacetype == SPACE_SCRIPT )
		sc = curarea->spacedata.first;
	else
		return EXPP_incr_ret( Py_None );

	if( !PyArg_ParseTuple( args, "" ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected empty argument list" );

	exit_pydraw( sc, 0 );

	script = sc->script;

	/* remove our lock to the current namespace */
	script->flags &= ~SCRIPT_GUI;

	return EXPP_incr_ret( Py_None );
}

/* Method_Register (Draw.Register) registers callbacks for drawing, events
 * and gui button events, so a script can continue executing after the
 * interpreter reached its end and returned control to Blender.  Everytime
 * the SPACE_SCRIPT window with this script is redrawn, the registered
 * callbacks are executed. */
static PyObject *Method_Register( PyObject * self, PyObject * args )
{
	PyObject *newdrawc = NULL, *neweventc = NULL, *newbuttonc = NULL;
	SpaceScript *sc;
	Script *script;
	int startspace = 0;

	if( !PyArg_ParseTuple
	    ( args, "O|OO", &newdrawc, &neweventc, &newbuttonc ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected one or three PyObjects" );

	if( !PyCallable_Check( newdrawc ) )
		newdrawc = NULL;
	if( !PyCallable_Check( neweventc ) )
		neweventc = NULL;
	if( !PyCallable_Check( newbuttonc ) )
		newbuttonc = NULL;

	if( !( newdrawc || neweventc || newbuttonc ) )
		return EXPP_incr_ret( Py_None );

	startspace = curarea->spacetype;

	/* first make sure the current area is of type SPACE_SCRIPT */
	if( startspace != SPACE_SCRIPT )
		newspace( curarea, SPACE_SCRIPT );

	sc = curarea->spacedata.first;

	/* There are two kinds of scripts:
	 * a) those that simply run, finish and return control to Blender;
	 * b) those that do like 'a)' above but leave callbacks for drawing,
	 * events and button events, with this Method_Register (Draw.Register
	 * in Python).  These callbacks are called by scriptspaces (Scripts windows).
	 *
	 * We need to flag scripts that leave callbacks so their namespaces are
	 * not deleted when they 'finish' execution, because the callbacks will
	 * still need the namespace.
	 */

	/* Let's see if this is a new script */
	script = G.main->script.first;
	while (script) {
		if (script->flags & SCRIPT_RUNNING) break;
		script = script->id.next;
	}

	if( !script ) {
		/* not new, it's a left callback calling Register again */
 		script = sc->script;
		if( !script ) {
			return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"Draw.Register can't be used inside script links" );
		}
	}
	else sc->script = script;

	/* Now we have the right script and can set a lock so its namespace can't be
	 * deleted for as long as we need it */
	script->flags |= SCRIPT_GUI;

	/* save the last space so we can go back to it upon finishing */
	if( !script->lastspace )
		script->lastspace = startspace;

	/* clean the old callbacks */
	exit_pydraw( sc, 0 );

	/* prepare the new ones and insert them */
	Py_XINCREF( newdrawc );
	Py_XINCREF( neweventc );
	Py_XINCREF( newbuttonc );

	script->py_draw = newdrawc;
	script->py_event = neweventc;
	script->py_button = newbuttonc;

	scrarea_queue_redraw( sc->area );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Method_Redraw( PyObject * self, PyObject * args )
{
	int after = 0;

	if( !PyArg_ParseTuple( args, "|i", &after ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument (or nothing)" );

	if( after )
		addafterqueue( curarea->win, REDRAW, 1 );
	else
		scrarea_queue_winredraw( curarea );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Method_Draw( PyObject * self, PyObject * args )
{
	/*@ If forced drawing is disable queue a redraw event instead */
	if( EXPP_disable_force_draw ) {
		scrarea_queue_winredraw( curarea );
		return EXPP_incr_ret( Py_None );
	}

	if( !PyArg_ParseTuple( args, "" ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected empty argument list" );

	scrarea_do_windraw( curarea );

	screen_swapbuffers(  );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Method_Create( PyObject * self, PyObject * args )
{
	Button *but;
	PyObject *in;

	if( !PyArg_ParseTuple( args, "O", &in ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected PyObject argument" );

	but = newbutton(  );
	if( PyFloat_Check( in ) ) {
		but->type = 2;
		but->val.asfloat = (float)PyFloat_AsDouble( in );
	} else if( PyInt_Check( in ) ) {
		but->type = 1;
		but->val.asint = PyInt_AsLong( in );
	} else if( PyString_Check( in ) ) {
		char *newstr = PyString_AsString( in );

		but->type = 3;
		but->slen = strlen( newstr );
		but->val.asstr = MEM_mallocN( but->slen + 1, "button string" );

		strcpy( but->val.asstr, newstr );
	}

	return ( PyObject * ) but;
}

static uiBlock *Get_uiBlock( void )
{
	char butblock[32];

	sprintf( butblock, "win %d", curarea->win );

	return uiGetBlock( butblock, curarea );
}

/* We restrict the acceptable event numbers to a proper "free" range
 * according to other spaces in Blender.
 * winqread***space() (space events callbacks) use short for events
 * (called 'val' there) and we also translate by EXPP_BUTTON_EVENTS_OFFSET
 * to get rid of unwanted events (check BPY_do_pywin_events above for
 * explanation). This function takes care of that and proper checking: */
static int check_button_event(int *event) {
	if ((*event < EXPP_BUTTON_EVENTS_MIN) ||
			(*event > EXPP_BUTTON_EVENTS_MAX)) {
		return -1;
	}
	*event += EXPP_BUTTON_EVENTS_OFFSET;
	return 0;
}

static PyObject *Method_Button( PyObject * self, PyObject * args )
{
	uiBlock *block;
	char *name, *tip = NULL;
	int event;
	int x, y, w, h;

	if( !PyArg_ParseTuple( args, "siiiii|s", &name, &event,
			       &x, &y, &w, &h, &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a string, five ints and optionally another string as arguments" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	block = Get_uiBlock(  );

	if( block )
		uiDefBut( block, BUT, event, name, (short)x, (short)y, (short)w, (short)h, 0, 0, 0, 0, 0,
			  tip );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Method_Menu( PyObject * self, PyObject * args )
{
	uiBlock *block;
	char *name, *tip = NULL;
	int event, def;
	int x, y, w, h;
	Button *but;

	if( !PyArg_ParseTuple( args, "siiiiii|s", &name, &event,
			       &x, &y, &w, &h, &def, &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a string, six ints and optionally another string as arguments" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	but = newbutton(  );
	but->type = 1;
	but->val.asint = def;

	block = Get_uiBlock(  );
	if( block )
		uiDefButI( block, MENU, event, name, (short)x, (short)y, (short)w, (short)h,
			   &but->val.asint, 0, 0, 0, 0, tip );

	return ( PyObject * ) but;
}

static PyObject *Method_Toggle( PyObject * self, PyObject * args )
{
	uiBlock *block;
	char *name, *tip = NULL;
	int event;
	int x, y, w, h, def;
	Button *but;

	if( !PyArg_ParseTuple( args, "siiiiii|s", &name, &event,
			       &x, &y, &w, &h, &def, &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a string, six ints and optionally another string as arguments" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	but = newbutton(  );
	but->type = 1;
	but->val.asint = def;

	block = Get_uiBlock(  );
	if( block )
		uiDefButI( block, TOG, event, name, (short)x, (short)y, (short)w, (short)h,
			   &but->val.asint, 0, 0, 0, 0, tip );

	return ( PyObject * ) but;
}

/*@DO NOT TOUCH THIS FUNCTION !
	 Redrawing a slider inside its own callback routine is actually forbidden
	 with the current toolkit architecture (button routines are not reentrant).
	 But it works anyway.
	 XXX This is condemned to be dinosource in future - it's a hack.
	 */

static void py_slider_update( void *butv, void *data2_unused )
{
	uiBut *but = butv;
	PyObject *ref = Py_BuildValue( "(i)", SPACE_VIEW3D );
	PyObject *ret = NULL;

	EXPP_disable_force_draw = 1;
	/*@ Disable forced drawing, otherwise the button object which
	 * is still being used might be deleted */

	curarea->win_swap = WIN_BACK_OK;
	/* removed global uiFrontBuf (contact ton when this goes wrong here) */

	disable_where_script( 1 );

	spacescript_do_pywin_buttons( curarea->spacedata.first,
		(unsigned short)uiButGetRetVal( but ) );

	/* XXX useless right now, investigate better before a bcon 5 */
	ret = M_Window_Redraw( 0, ref );

	Py_DECREF(ref);
	if (ret) { Py_DECREF(ret); }

	disable_where_script( 0 );

	EXPP_disable_force_draw = 0;
}

static PyObject *Method_Slider( PyObject * self, PyObject * args )
{
	uiBlock *block;
	char *name, *tip = NULL;
	int event;
	int x, y, w, h, realtime = 1;
	Button *but;
	PyObject *mino, *maxo, *inio;

	if( !PyArg_ParseTuple( args, "siiiiiOOO|is", &name, &event,
			       &x, &y, &w, &h, &inio, &mino, &maxo, &realtime,
			       &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a string, five ints, three PyObjects\n\
			and optionally another int and string as arguments" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	but = newbutton(  );

	if( PyFloat_Check( inio ) ) {
		float ini, min, max;

		ini = (float)PyFloat_AsDouble( inio );
		min = (float)PyFloat_AsDouble( mino );
		max = (float)PyFloat_AsDouble( maxo );

		but->type = 2;
		but->val.asfloat = ini;

		block = Get_uiBlock(  );
		if( block ) {
			uiBut *ubut;
			ubut = uiDefButF( block, NUMSLI, event, name, (short)x, (short)y, (short)w,
					  (short)h, &but->val.asfloat, min, max, 0, 0,
					  tip );
			if( realtime )
				uiButSetFunc( ubut, py_slider_update, ubut,
					      NULL );
		}
	} else {
		int ini, min, max;

		ini = PyInt_AsLong( inio );
		min = PyInt_AsLong( mino );
		max = PyInt_AsLong( maxo );

		but->type = 1;
		but->val.asint = ini;

		block = Get_uiBlock(  );
		if( block ) {
			uiBut *ubut;
			ubut = uiDefButI( block, NUMSLI, event, name, (short)x, (short)y, (short)w,
					  (short)h, &but->val.asint, (float)min, (float)max, 0, 0,
					  tip );
			if( realtime )
				uiButSetFunc( ubut, py_slider_update, ubut,
					      NULL );
		}
	}
	return ( PyObject * ) but;
}

static PyObject *Method_Scrollbar( PyObject * self, PyObject * args )
{
	char *tip = NULL;
	uiBlock *block;
	int event;
	int x, y, w, h, realtime = 1;
	Button *but;
	PyObject *mino, *maxo, *inio;
	float ini, min, max;

	if( !PyArg_ParseTuple( args, "iiiiiOOO|is", &event, &x, &y, &w, &h,
			       &inio, &mino, &maxo, &realtime, &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
			"expected five ints, three PyObjects and optionally\n\
another int and string as arguments" );

	if( !PyNumber_Check( inio ) || !PyNumber_Check( inio )
	    || !PyNumber_Check( inio ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected numbers for initial, min, and max" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	but = newbutton(  );

	if( PyFloat_Check( inio ) )
		but->type = 2;
	else
		but->type = 1;

	ini = (float)PyFloat_AsDouble( inio );
	min = (float)PyFloat_AsDouble( mino );
	max = (float)PyFloat_AsDouble( maxo );

	if( but->type == 2 ) {
		but->val.asfloat = ini;
		block = Get_uiBlock(  );
		if( block ) {
			uiBut *ubut;
			ubut = uiDefButF( block, SCROLL, event, "", (short)x, (short)y, (short)w, (short)h,
					  &but->val.asfloat, min, max, 0, 0,
					  tip );
			if( realtime )
				uiButSetFunc( ubut, py_slider_update, ubut,
					      NULL );
		}
	} else {
		but->val.asint = (int)ini;
		block = Get_uiBlock(  );
		if( block ) {
			uiBut *ubut;
			ubut = uiDefButI( block, SCROLL, event, "", (short)x, (short)y, (short)w, (short)h,
					  &but->val.asint, min, max, 0, 0,
					  tip );
			if( realtime )
				uiButSetFunc( ubut, py_slider_update, ubut,
					      NULL );
		}
	}

	return ( PyObject * ) but;
}

static PyObject *Method_Number( PyObject * self, PyObject * args )
{
	uiBlock *block;
	char *name, *tip = NULL;
	int event;
	int x, y, w, h;
	Button *but;
	PyObject *mino, *maxo, *inio;

	if( !PyArg_ParseTuple( args, "siiiiiOOO|s", &name, &event,
			       &x, &y, &w, &h, &inio, &mino, &maxo, &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a string, five ints, three PyObjects and\n\
			optionally another string as arguments" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	but = newbutton(  );

	if( PyFloat_Check( inio ) ) {
		float ini, min, max;

		ini = (float)PyFloat_AsDouble( inio );
		min = (float)PyFloat_AsDouble( mino );
		max = (float)PyFloat_AsDouble( maxo );

		but->type = 2;
		but->val.asfloat = ini;

		block = Get_uiBlock(  );
		if( block )
			uiDefButF( block, NUM, event, name, (short)x, (short)y, (short)w, (short)h,
				   &but->val.asfloat, min, max, 0, 0, tip );
	} else {
		int ini, min, max;

		ini = PyInt_AsLong( inio );
		min = PyInt_AsLong( mino );
		max = PyInt_AsLong( maxo );

		but->type = 1;
		but->val.asint = ini;

		block = Get_uiBlock(  );
		if( block )
			uiDefButI( block, NUM, event, name, (short)x, (short)y, (short)w, (short)h,
				   &but->val.asint, (float)min, (float)max, 0, 0, tip );
	}

	return ( PyObject * ) but;
}

static PyObject *Method_String( PyObject * self, PyObject * args )
{
	uiBlock *block;
	char *info_arg = NULL, *tip = NULL, *newstr = NULL;
	char *info_str = NULL, *info_str0 = " ";
	int event;
	int x, y, w, h, len, real_len = 0;
	Button *but;

	if( !PyArg_ParseTuple( args, "siiiiisi|s", &info_arg, &event,
			&x, &y, &w, &h, &newstr, &len, &tip ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
			"expected a string, five ints, a string, an int and\n\
	optionally another string as arguments" );

	if (check_button_event(&event) == -1)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"button event argument must be in the range [0, 16382]");

	if (len > (UI_MAX_DRAW_STR - 1)) {
		len = UI_MAX_DRAW_STR - 1;
		newstr[len] = '\0';
	}

	real_len = strlen(newstr);
	if (real_len > len) real_len = len;

	but = newbutton(  );
	but->type = 3;
	but->slen = len;
	but->val.asstr = MEM_mallocN( len + 1, "pybutton str" );

	BLI_strncpy( but->val.asstr, newstr, len + 1); /* adds '\0' */
	but->val.asstr[real_len] = '\0';

	if (info_arg[0] == '\0') info_str = info_str0;
	else info_str = info_arg;

	block = Get_uiBlock(  );
	if( block )
		uiDefBut( block, TEX, event, info_str, (short)x, (short)y, (short)w, (short)h,
			  but->val.asstr, 0, (float)len, 0, 0, tip );

	return ( PyObject * ) but;
}

static PyObject *Method_GetStringWidth( PyObject * self, PyObject * args )
{
	char *text;
	char *font_str = "normal";
	struct BMF_Font *font;
	PyObject *width;

	if( !PyArg_ParseTuple( args, "s|s", &text, &font_str ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected one or two string arguments" );

	if( !strcmp( font_str, "normal" ) )
		font = ( &G )->font;
	else if( !strcmp( font_str, "large" ) )
		font = BMF_GetFont(BMF_kScreen15);
	else if( !strcmp( font_str, "small" ) )
		font = ( &G )->fonts;
	else if( !strcmp( font_str, "tiny" ) )
		font = ( &G )->fontss;
	else
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "\"font\" must be: 'large', 'normal' (default), 'small' or 'tiny'." );

	width = PyInt_FromLong( BMF_GetStringWidth( font, text ) );

	if( !width )
		return EXPP_ReturnPyObjError( PyExc_MemoryError,
					      "couldn't create PyInt" );

	return width;
}

static PyObject *Method_Text( PyObject * self, PyObject * args )
{
	char *text;
	char *font_str = NULL;
	struct BMF_Font *font;

	if( !PyArg_ParseTuple( args, "s|s", &text, &font_str ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected one or two string arguments" );

	if( !font_str )
		font = ( &G )->font;
	else if( !strcmp( font_str, "large" ) )
		font = BMF_GetFont(BMF_kScreen15);
	else if( !strcmp( font_str, "normal" ) )
		font = ( &G )->font;
	else if( !strcmp( font_str, "small" ) )
		font = ( &G )->fonts;
	else if( !strcmp( font_str, "tiny" ) )
		font = ( &G )->fontss;
	else
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "\"font\" must be: 'normal' (default), 'large', 'small' or 'tiny'." );

	BMF_DrawString( font, text );

	return PyInt_FromLong( BMF_GetStringWidth( font, text ) );
}

static PyObject *Method_PupMenu( PyObject * self, PyObject * args )
{
	char *text;
	int maxrow = -1;
	PyObject *ret;

	if( !PyArg_ParseTuple( args, "s|i", &text, &maxrow ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a string and optionally an int as arguments" );

	if( maxrow >= 0 )
		ret = PyInt_FromLong( pupmenu_col( text, maxrow ) );
	else
		ret = PyInt_FromLong( pupmenu( text ) );

	if( ret )
		return ret;

	return EXPP_ReturnPyObjError( PyExc_MemoryError,
				      "couldn't create a PyInt" );
}

static PyObject *Method_PupIntInput( PyObject * self, PyObject * args )
{
	char *text = NULL;
	int min = 0, max = 1;
	short var = 0;
	PyObject *ret = NULL;

	if( !PyArg_ParseTuple( args, "s|hii", &text, &var, &min, &max ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected 1 string and 3 int arguments" );

	if( button( &var, (short)min, (short)max, text ) == 0 ) {
		Py_INCREF( Py_None );
		return Py_None;
	}
	ret = PyInt_FromLong( var );
	if( ret )
		return ret;

	return EXPP_ReturnPyObjError( PyExc_MemoryError,
				      "couldn't create a PyInt" );
}

static PyObject *Method_PupFloatInput( PyObject * self, PyObject * args )
{
	char *text = NULL;
	float min = 0, max = 1, var = 0, a1 = 10, a2 = 2;
	PyObject *ret = NULL;

	if( !PyArg_ParseTuple
	    ( args, "s|fffff", &text, &var, &min, &max, &a1, &a2 ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected 1 string and 5 float arguments" );

	if( fbutton( &var, min, max, a1, a2, text ) == 0 ) {
		Py_INCREF( Py_None );
		return Py_None;
	}
	ret = PyFloat_FromDouble( var );
	if( ret )
		return ret;

	return EXPP_ReturnPyObjError( PyExc_MemoryError,
				      "couldn't create a PyFloat" );
}

static PyObject *Method_PupStrInput( PyObject * self, PyObject * args )
{
	char *text = NULL, *textMsg = NULL;
	char tmp[101];
	char max = 20;
	PyObject *ret = NULL;

	if( !PyArg_ParseTuple( args, "ss|b", &textMsg, &text, &max ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected 2 strings and 1 int" );

	if( ( max <= 0 ) || ( max > 100 ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "max string length value must be in the range [1, 100]." );

	/* copying the text string handles both cases:
	 * max < strlen(text) (by truncating) and
	 * max > strlen(text) (by expanding to strlen(tmp)) */
	BLI_strncpy( tmp, text, max + 1 );

	if( sbutton( tmp, 0, max, textMsg ) == 0 ) {
		Py_INCREF( Py_None );
		return Py_None;
	}

	ret = Py_BuildValue( "s", tmp );

	if( ret )
		return ret;

	return EXPP_ReturnPyObjError( PyExc_MemoryError,
				      "couldn't create a PyString" );
}

/*****************************************************************************
 * Function:            Method_Image                                         *
 * Python equivalent:   Blender.Draw.Image                                   *
 *                                                                           *
 * @author Jonathan Merritt <j.merritt@pgrad.unimelb.edu.au>                 *
 ****************************************************************************/
static PyObject *Method_Image( PyObject * self, PyObject * args )
{
	PyObject *pyObjImage;
	BPy_Image *py_img;
	Image *image;
	float originX, originY;
	float zoomX = 1.0, zoomY = 1.0;
	int clipX = 0, clipY = 0, clipW = -1, clipH = -1;
	/*GLfloat scissorBox[4];*/

	/* parse the arguments passed-in from Python */
	if( !PyArg_ParseTuple( args, "Off|ffiiii", &pyObjImage, 
		&originX, &originY, &zoomX, &zoomY, 
		&clipX, &clipY, &clipW, &clipH ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
			"expected a Blender.Image and 2 floats, and " \
			"optionally 2 floats and 4 ints as arguments" );
	/* check that the first PyObject is actually a Blender.Image */
	if( !Image_CheckPyObject( pyObjImage ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
			"expected a Blender.Image and 2 floats, and " \
			"optionally 2 floats and 4 ints as arguments" );
	/* check that the zoom factors are valid */
	if( ( zoomX <= 0.0 ) || ( zoomY <= 0.0 ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
			"invalid zoom factors - they must be >= 0.0" );

	/* fetch a C Image pointer from the passed-in Python object */
	py_img = ( BPy_Image * ) pyObjImage;
	image = py_img->image;

	/* load the image data if necessary */
	if( !image->ibuf )      /* if no image data is available ... */
		load_image( image, IB_rect, "", 0 );    /* ... load it */
	if( !image->ibuf )      /* if failed to load the image */
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
			"couldn't load image data in Blender" );

	/* Update the time tag of the image */
	tag_image_time(image);

	/* set up a valid clipping rectangle.  if no clip rectangle was
	 * given, this results in inclusion of the entire image.  otherwise,
	 * the clipping is just checked against the bounds of the image.
	 * if clipW or clipH are less than zero then they include as much of
	 * the image as they can. */
	clipX = EXPP_ClampInt( clipX, 0, image->ibuf->x );
	clipY = EXPP_ClampInt( clipY, 0, image->ibuf->y );
	if( ( clipW < 0 ) || ( clipW > ( image->ibuf->x - clipW ) ) )
		clipW = image->ibuf->x - clipX;
	if( ( clipH < 0 ) || ( clipH > ( image->ibuf->y - clipH ) ) )
		clipH = image->ibuf->y - clipY;

	/* -- we are "Go" to Draw! -- */

	/* set the raster position.
	 *
	 * If the raster position is negative, then using glRasterPos2i() 
	 * directly would cause it to be clipped.  Instead, we first establish 
	 * a valid raster position within the clipping rectangle of the 
	 * window and then use glBitmap() with a NULL image pointer to offset 
	 * it to the true position we require.  To pick an initial valid 
	 * raster position within the viewport, we query the clipping rectangle
	 * and use its lower-left pixel.
	 *
	 * This particular technique is documented in the glRasterPos() man
	 * page, although I haven't seen it used elsewhere in Blender.
	 */

	/* update (W): to fix a bug where images wouldn't get drawn if the bottom
	 * left corner of the Scripts win were above a given height or to the right
	 * of a given width, the code below is being commented out.  It should not
	 * be needed anyway, because spaces in Blender are projected to lie inside
	 * their areas, see src/drawscript.c for example.  Note: the
	 * glaRasterPosSafe2i function in src/glutil.c does use the commented out
	 * technique, but with 0,0 instead of scissorBox.  This function can be
	 * a little optimized, based on glaDrawPixelsSafe in that same fine, but
	 * we're too close to release 2.37 right now. */
	/*
	glGetFloatv( GL_SCISSOR_BOX, scissorBox );
	glRasterPos2i( scissorBox[0], scissorBox[1] );
	glBitmap( 0, 0, 0.0, 0.0, 
		originX-scissorBox[0], originY-scissorBox[1], NULL );
	*/

	/* update (cont.): using these two lines instead:
	 * (based on glaRasterPosSafe2i, but Ken Hughes deserves credit
	 * for suggesting this exact fix in the bug tracker) */
	glRasterPos2i(0, 0);
	glBitmap( 0, 0, 0.0, 0.0, originX, originY, NULL );

	/* set the zoom */
	glPixelZoom( zoomX, zoomY );

	/* set the width of the image (ROW_LENGTH), and the offset to the
	 * clip origin within the image in x (SKIP_PIXELS) and 
	 * y (SKIP_ROWS) */
	glPixelStorei( GL_UNPACK_ROW_LENGTH,  image->ibuf->x );
	glPixelStorei( GL_UNPACK_SKIP_PIXELS, clipX );
	glPixelStorei( GL_UNPACK_SKIP_ROWS,   clipY );

	/* draw the image */
	glDrawPixels( clipW, clipH, GL_RGBA, GL_UNSIGNED_BYTE, 
		image->ibuf->rect );

	/* restore the defaults for some parameters (we could also use a
	 * glPushClientAttrib() and glPopClientAttrib() pair). */
	glPixelZoom( 1.0, 1.0 );
	glPixelStorei( GL_UNPACK_SKIP_ROWS,   0 );
	glPixelStorei( GL_UNPACK_SKIP_PIXELS, 0 );
	glPixelStorei( GL_UNPACK_ROW_LENGTH,  0 );

	Py_INCREF( Py_None );
	return Py_None;

}

PyObject *Draw_Init( void )
{
	PyObject *submodule, *dict;

	Button_Type.ob_type = &PyType_Type;

	submodule = Py_InitModule3( "Blender.Draw", Draw_methods, Draw_doc );

	dict = PyModule_GetDict( submodule );

#define EXPP_ADDCONST(x) \
	PyDict_SetItemString(dict, #x, PyInt_FromLong(x))

	/* So, for example:
	 * EXPP_ADDCONST(LEFTMOUSE) becomes
	 * PyDict_SetItemString(dict, "LEFTMOUSE", PyInt_FromLong(LEFTMOUSE)) 
	 */

	EXPP_ADDCONST( LEFTMOUSE );
	EXPP_ADDCONST( MIDDLEMOUSE );
	EXPP_ADDCONST( RIGHTMOUSE );
	EXPP_ADDCONST( WHEELUPMOUSE );
	EXPP_ADDCONST( WHEELDOWNMOUSE );
	EXPP_ADDCONST( MOUSEX );
	EXPP_ADDCONST( MOUSEY );
	EXPP_ADDCONST( TIMER0 );
	EXPP_ADDCONST( TIMER1 );
	EXPP_ADDCONST( TIMER2 );
	EXPP_ADDCONST( TIMER3 );
	EXPP_ADDCONST( KEYBD );
	EXPP_ADDCONST( RAWKEYBD );
	EXPP_ADDCONST( REDRAW );
	EXPP_ADDCONST( INPUTCHANGE );
	EXPP_ADDCONST( QFULL );
	EXPP_ADDCONST( WINFREEZE );
	EXPP_ADDCONST( WINTHAW );
	EXPP_ADDCONST( WINCLOSE );
	EXPP_ADDCONST( WINQUIT );
#ifndef IRISGL
	EXPP_ADDCONST( Q_FIRSTTIME );
#endif
	EXPP_ADDCONST( AKEY );
	EXPP_ADDCONST( BKEY );
	EXPP_ADDCONST( CKEY );
	EXPP_ADDCONST( DKEY );
	EXPP_ADDCONST( EKEY );
	EXPP_ADDCONST( FKEY );
	EXPP_ADDCONST( GKEY );
	EXPP_ADDCONST( HKEY );
	EXPP_ADDCONST( IKEY );
	EXPP_ADDCONST( JKEY );
	EXPP_ADDCONST( KKEY );
	EXPP_ADDCONST( LKEY );
	EXPP_ADDCONST( MKEY );
	EXPP_ADDCONST( NKEY );
	EXPP_ADDCONST( OKEY );
	EXPP_ADDCONST( PKEY );
	EXPP_ADDCONST( QKEY );
	EXPP_ADDCONST( RKEY );
	EXPP_ADDCONST( SKEY );
	EXPP_ADDCONST( TKEY );
	EXPP_ADDCONST( UKEY );
	EXPP_ADDCONST( VKEY );
	EXPP_ADDCONST( WKEY );
	EXPP_ADDCONST( XKEY );
	EXPP_ADDCONST( YKEY );
	EXPP_ADDCONST( ZKEY );
	EXPP_ADDCONST( ZEROKEY );
	EXPP_ADDCONST( ONEKEY );
	EXPP_ADDCONST( TWOKEY );
	EXPP_ADDCONST( THREEKEY );
	EXPP_ADDCONST( FOURKEY );
	EXPP_ADDCONST( FIVEKEY );
	EXPP_ADDCONST( SIXKEY );
	EXPP_ADDCONST( SEVENKEY );
	EXPP_ADDCONST( EIGHTKEY );
	EXPP_ADDCONST( NINEKEY );
	EXPP_ADDCONST( CAPSLOCKKEY );
	EXPP_ADDCONST( LEFTCTRLKEY );
	EXPP_ADDCONST( LEFTALTKEY );
	EXPP_ADDCONST( RIGHTALTKEY );
	EXPP_ADDCONST( RIGHTCTRLKEY );
	EXPP_ADDCONST( RIGHTSHIFTKEY );
	EXPP_ADDCONST( LEFTSHIFTKEY );
	EXPP_ADDCONST( ESCKEY );
	EXPP_ADDCONST( TABKEY );
	EXPP_ADDCONST( RETKEY );
	EXPP_ADDCONST( SPACEKEY );
	EXPP_ADDCONST( LINEFEEDKEY );
	EXPP_ADDCONST( BACKSPACEKEY );
	EXPP_ADDCONST( DELKEY );
	EXPP_ADDCONST( SEMICOLONKEY );
	EXPP_ADDCONST( PERIODKEY );
	EXPP_ADDCONST( COMMAKEY );
	EXPP_ADDCONST( QUOTEKEY );
	EXPP_ADDCONST( ACCENTGRAVEKEY );
	EXPP_ADDCONST( MINUSKEY );
	EXPP_ADDCONST( SLASHKEY );
	EXPP_ADDCONST( BACKSLASHKEY );
	EXPP_ADDCONST( EQUALKEY );
	EXPP_ADDCONST( LEFTBRACKETKEY );
	EXPP_ADDCONST( RIGHTBRACKETKEY );
	EXPP_ADDCONST( LEFTARROWKEY );
	EXPP_ADDCONST( DOWNARROWKEY );
	EXPP_ADDCONST( RIGHTARROWKEY );
	EXPP_ADDCONST( UPARROWKEY );
	EXPP_ADDCONST( PAD2 );
	EXPP_ADDCONST( PAD4 );
	EXPP_ADDCONST( PAD6 );
	EXPP_ADDCONST( PAD8 );
	EXPP_ADDCONST( PAD1 );
	EXPP_ADDCONST( PAD3 );
	EXPP_ADDCONST( PAD5 );
	EXPP_ADDCONST( PAD7 );
	EXPP_ADDCONST( PAD9 );
	EXPP_ADDCONST( PADPERIOD );
	EXPP_ADDCONST( PADSLASHKEY );
	EXPP_ADDCONST( PADASTERKEY );
	EXPP_ADDCONST( PAD0 );
	EXPP_ADDCONST( PADMINUS );
	EXPP_ADDCONST( PADENTER );
	EXPP_ADDCONST( PADPLUSKEY );
	EXPP_ADDCONST( F1KEY );
	EXPP_ADDCONST( F2KEY );
	EXPP_ADDCONST( F3KEY );
	EXPP_ADDCONST( F4KEY );
	EXPP_ADDCONST( F5KEY );
	EXPP_ADDCONST( F6KEY );
	EXPP_ADDCONST( F7KEY );
	EXPP_ADDCONST( F8KEY );
	EXPP_ADDCONST( F9KEY );
	EXPP_ADDCONST( F10KEY );
	EXPP_ADDCONST( F11KEY );
	EXPP_ADDCONST( F12KEY );
	EXPP_ADDCONST( PAUSEKEY );
	EXPP_ADDCONST( INSERTKEY );
	EXPP_ADDCONST( HOMEKEY );
	EXPP_ADDCONST( PAGEUPKEY );
	EXPP_ADDCONST( PAGEDOWNKEY );
	EXPP_ADDCONST( ENDKEY );

	return submodule;
}
