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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef WM_TYPES_H
#define WM_TYPES_H

struct bContext;
struct wmEvent;

/* exported types for WM */

#include "wm_cursors.h"
#include "wm_event_types.h"

/* ************** wmOperatorType ************************ */

/* flag */
#define OPTYPE_REGISTER		1

/* context to call operator in for WM_operator_name_call */
enum {
	WM_OP_INVOKE_DEFAULT,
	WM_OP_INVOKE_REGION_WIN,
	WM_OP_INVOKE_AREA,
	WM_OP_INVOKE_SCREEN,
	WM_OP_EXEC_DEFAULT,
	WM_OP_EXEC_REGION_WIN,
	WM_OP_EXEC_AREA,
	WM_OP_EXEC_SCREEN
};

/* ************** wmEvent ************************ */

/* each event should have full modifier state */
/* event comes from eventmanager and from keymap */
typedef struct wmEvent {
	struct wmEvent *next, *prev;
	
	short type;		/* event code itself (short, is also in keymap) */
	short val;		/* press, release, scrollvalue */
	short x, y;				/* mouse pointer position */
	short prevx, prevy;		/* previous mouse pointer position */
	short unicode;	/* future, ghost? */
	char ascii;		/* from ghost */
	char pad1;		
	
	/* modifier states */
	short shift, ctrl, alt, oskey;	/* oskey is apple or windowskey, value denotes order of pressed */
	short keymodifier;				/* rawkey modifier */
	
	/* keymap item, set by handler (weak?) */
	const char *keymap_idname;
	
	/* custom data */
	short custom;	/* custom data type, stylus, 6dof, see wm_event_types.h */
	void *customdata;	/* ascii, unicode, mouse coords, angles, vectors, dragdrop info */
	short customdatafree;
	
} wmEvent;


/* ************** wmKeyMap ************************ */

/* modifier */
#define KM_SHIFT	1
#define KM_CTRL		2
#define KM_ALT		4
#define KM_OSKEY	8
	/* means modifier should be pressed 2nd */
#define KM_SHIFT2	16
#define KM_CTRL2	32
#define KM_ALT2		64
#define KM_OSKEY2	128

/* val */
#define KM_ANY		-1
#define KM_RELEASE	0
#define KM_PRESS	1

/* ************** UI Handler ***************** */

#define WM_UI_HANDLER_CONTINUE	0
#define WM_UI_HANDLER_BREAK		1

typedef int (*wmUIHandlerFunc)(struct bContext *C, struct wmEvent *event, void *userdata);
typedef void (*wmUIHandlerRemoveFunc)(struct bContext *C, void *userdata);

/* ************** Notifiers ****************** */

typedef struct wmNotifier {
	struct wmNotifier *prev, *next;
	
	struct wmWindow *window;
	
	int swinid;
	int type;
	int value;
	void *data;
	
} wmNotifier;


enum {
	WM_NOTE_WINDOW_REDRAW,
	WM_NOTE_SCREEN_CHANGED,
	WM_NOTE_GESTURE_REDRAW,
	WM_NOTE_MARKERS_CHANGED,
	WM_NOTE_OBJECT_CHANGED,
	WM_NOTE_LAST
};

/* ************** Gesture Manager data ************** */

/* wmGesture->type */
#define WM_GESTURE_TWEAK		0
#define WM_GESTURE_LINE			1
#define WM_GESTURE_RECT			2
#define WM_GESTURE_CROSS_RECT	3
#define WM_GESTURE_LASSO		4
#define WM_GESTURE_CIRCLE		5

/* wmGesture is registered to window listbase, handled by operator callbacks */
typedef struct wmGesture {
	struct wmGesture *next, *prev;
	int event_type;	/* event->type */
	int mode;		/* for modal callback */
	int type;		/* gesture type define */
	int swinid;		/* initial subwindow id where it started */
	
	void *customdata;
	/* customdata for border is a recti */
	/* customdata for circle is recti, (xmin, ymin) is center, xmax radius */
	
} wmGesture;


/* ************** custom wmEvent data ************** */

#define DEV_STYLUS	1
#define DEV_ERASER  2

typedef struct wmTabletData {
	int Active;			/* 0=None, 1=Stylus, 2=Eraser */
	float Pressure;		/* range 0.0 (not touching) to 1.0 (full pressure) */
	float Xtilt;		/* range 0.0 (upright) to 1.0 (tilted fully against the tablet surface) */
	float Ytilt;		/* as above */
} wmTabletData;

typedef struct wmTimer {
	struct wmTimer *next, *prev;
	double timestep;		/* set by timer user */
	
	double duration;		/* total running time in seconds */
	double delta;			/* time since previous step in seconds */
	
	double ltime;			/* internal, last time timer was activated */
	int sleep;				/* internal, put timers to sleep when needed */
} wmTimer;


/* ****************** Messages ********************* */

enum {
	WM_LOG_DEBUG				= 0,
	WM_LOG_INFO					= 1000,
	WM_LOG_WARNING				= 2000,
	WM_ERROR_UNDEFINED			= 3000,
	WM_ERROR_INVALID_INPUT		= 3001,
	WM_ERROR_INVALID_CONTEXT	= 3002,
	WM_ERROR_OUT_OF_MEMORY		= 3003
};

typedef struct wmReport {
	struct wmReport *next, *prev;
	int type;
	const char *typestr;
	char *message;
} wmReport;

/* *************** migrated stuff, clean later? ******************************** */

typedef struct RecentFile {
	struct RecentFile *next, *prev;
	char *filename;
} RecentFile;


#endif /* WM_TYPES_H */

