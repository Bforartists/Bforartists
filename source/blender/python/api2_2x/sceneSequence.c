/*
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
 * This is a new part of Blender.
 *
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "sceneSequence.h" /* This must come first */

#include "MEM_guardedalloc.h"

#include "DNA_sequence_types.h"
#include "DNA_scene_types.h" /* for Base */

#include "BKE_mesh.h"
#include "BKE_library.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_scene.h"

#include "BIF_editseq.h" /* get_last_seq */
#include "BLI_blenlib.h"
#include "BSE_sequence.h"
#include "Ipo.h"
#include "blendef.h"  /* CLAMP */
#include "BKE_utildefines.h"
#include "Scene.h"
#include "Sound.h"
#include "gen_utils.h"

enum seq_consts {
	EXPP_SEQ_ATTR_TYPE = 0,
	EXPP_SEQ_ATTR_CHAN,
	EXPP_SEQ_ATTR_LENGTH,
	EXPP_SEQ_ATTR_START,
	EXPP_SEQ_ATTR_STARTOFS,
	EXPP_SEQ_ATTR_ENDOFS
};


/*****************************************************************************/
/* Python API function prototypes for the Blender module.		 */
/*****************************************************************************/
/*PyObject *M_Sequence_Get( PyObject * self, PyObject * args );*/

/*****************************************************************************/
/* Python method structure definition for Blender.Object module:	 */
/*****************************************************************************/
/*struct PyMethodDef M_Sequence_methods[] = {
	{"Get", ( PyCFunction ) M_Sequence_Get, METH_VARARGS,
"(name) - return the sequence with the name 'name',\
returns None if notfound.\nIf 'name' is not specified, it returns a list of all sequences."},
	{NULL, NULL, 0, NULL}
};*/

/*****************************************************************************/
/* Python BPy_Sequence methods table:					   */
/*****************************************************************************/
static PyObject *Sequence_copy( BPy_Sequence * self );
static PyObject *Sequence_new( BPy_Sequence * self, PyObject * args );
static PyObject *Sequence_remove( BPy_Sequence * self, PyObject * args );

static PyObject *SceneSeq_new( BPy_SceneSeq * self, PyObject * args );
static PyObject *SceneSeq_remove( BPy_SceneSeq * self, PyObject * args );
static void intern_pos_update(Sequence * seq); 

static PyMethodDef BPy_Sequence_methods[] = {
	/* name, method, flags, doc */
	{"new", ( PyCFunction ) Sequence_new, METH_VARARGS,
	 "(data) - Return a new sequence."},
	{"remove", ( PyCFunction ) Sequence_remove, METH_VARARGS,
	 "(data) - Remove a strip."},
	{"__copy__", ( PyCFunction ) Sequence_copy, METH_NOARGS,
	 "() - Return a copy of the sequence containing the same objects."},
	{"copy", ( PyCFunction ) Sequence_copy, METH_NOARGS,
	 "() - Return a copy of the sequence containing the same objects."},
	{NULL, NULL, 0, NULL}
};

static PyMethodDef BPy_SceneSeq_methods[] = {
	/* name, method, flags, doc */
	{"new", ( PyCFunction ) SceneSeq_new, METH_VARARGS,
	 "(data) - Return a new sequence."},
	{"remove", ( PyCFunction ) SceneSeq_remove, METH_VARARGS,
	 "(data) - Remove a strip."},
	{NULL, NULL, 0, NULL}
};

/* use to add a sequence to a scene or its listbase */
static PyObject *NewSeq_internal(ListBase *seqbase, PyObject * args, Scene *sce)
{
	PyObject *py_data = NULL;
	
	Sequence *seq;
	int a;
	Strip *strip;
	StripElem *se;
	int start, machine;
	
	if( !PyArg_ParseTuple( args, "Oii", &py_data, &start, &machine ) )
		return EXPP_ReturnPyObjError( PyExc_ValueError,
			"expects a string for chan/bone name and an int for the frame where to put the new key" );
	
	seq = alloc_sequence(seqbase, start, machine); /* warning, this sets last */
	
	if (PyList_Check(py_data)) {
		/* Image */
		PyObject *list;
		char *name;
		
		if (!PyArg_ParseTuple( py_data, "sO!", &name, &PyList_Type, &list))
			return EXPP_ReturnPyObjError( PyExc_ValueError,
				"images data needs to be a tuple of a string and a list of images" );
		
		
		seq->type= SEQ_IMAGE;
		
		seq->len = PyList_Size( list );
		
		
		/* strip and stripdata */
		seq->strip= strip= MEM_callocN(sizeof(Strip), "strip");
		strip->len= seq->len;
		strip->us= 1;
		strncpy(strip->dir, name, FILE_MAXDIR-1);
		strip->stripdata= se= MEM_callocN(seq->len*sizeof(StripElem), "stripelem");

		for(a=0; a<seq->len; a++) {
			name = PyString_AsString(PyList_GetItem( list, a ));
			strncpy(se->name, name, FILE_MAXFILE-1);
			se->ok= 1;
			se++;
		}		
		
	} else if (BPy_Sound_Check(py_data)) {
		/* sound */
		int totframe;
		bSound *sound = (( BPy_Sound * )py_data)->sound;
		
		
		seq->type= SEQ_RAM_SOUND;
		seq->sound = sound;
		
		totframe= (int) ( ((float)(sound->streamlen-1)/( (float)sce->audio.mixrate*4.0 ))* (float)sce->r.frs_sec);
		
		sound->flags |= SOUND_FLAGS_SEQUENCE;
		
		
		/* strip and stripdata */
		seq->strip= strip= MEM_callocN(sizeof(Strip), "strip");
		strip->len= totframe;
		strip->us= 1;
		strncpy(strip->dir, sound->name, FILE_MAXDIR-1);
		strip->stripdata= se= MEM_callocN(totframe*sizeof(StripElem), "stripelem");

		/* name sound in first strip */
		strncpy(se->name, sound->name, FILE_MAXFILE-1);

		for(a=1; a<=totframe; a++, se++) {
			se->ok= 2; /* why? */
			se->ibuf= 0;
			se->nr= a;
		}
		
	} else if (BPy_Scene_Check(py_data)) {
		/* scene */
		Scene *sce = ((BPy_Scene *)py_data)->scene;
		
		seq->type= SEQ_SCENE;
		seq->scene= sce;
		
		/*seq->sfra= sce->r.sfra;*/
		seq->len= sce->r.efra - sce->r.sfra + 1;

		seq->strip= strip= MEM_callocN(sizeof(Strip), "strip");
		strncpy(seq->name + 2, sce->id.name + 2, 
			sizeof(seq->name) - 2);
		strip->len= seq->len;
		strip->us= 1;
		if(seq->len>0) strip->stripdata= MEM_callocN(seq->len*sizeof(StripElem), "stripelem");
		
	} else {
		char *name = PyString_AsString ( py_data );
		if (!name) {
			/* only free these 2 because other stuff isnt set */
			BLI_remlink(seqbase, seq);
			MEM_freeN(seq);
			
			return EXPP_ReturnPyObjError( PyExc_TypeError,
				"expects a string for chan/bone name and an int for the frame where to put the new key" );
		}
		
		/* movie */
		seq->type= SEQ_MOVIE;
	}
	
	intern_pos_update(seq);
	return Sequence_CreatePyObject(seq, NULL, sce);
}

static PyObject *Sequence_new( BPy_Sequence * self, PyObject * args )
{
	return NewSeq_internal(&self->seq->seqbase, args, self->scene);
}

static PyObject *SceneSeq_new( BPy_SceneSeq * self, PyObject * args )
{
	return NewSeq_internal( &((Editing *)self->scene->ed)->seqbase, args, self->scene);
}

static void del_seq__internal(Sequence *seq)
{
	if(seq->ipo) seq->ipo->id.us--;
	
	if(seq->type==SEQ_RAM_SOUND && seq->sound) 
		seq->sound->id.us--;
	free_sequence(seq);
}

static void recurs_del_seq(ListBase *lb)
{
	Sequence *seq, *seqn;

	seq= lb->first;
	while(seq) {
		seqn= seq->next;
		BLI_remlink(lb, seq);
		if(seq->type==SEQ_META) recurs_del_seq(&seq->seqbase);
		del_seq__internal(seq);
		seq= seqn;
	}
}

static PyObject *RemoveSeq_internal(ListBase *seqbase, PyObject * args, Scene *sce)
{
	BPy_Sequence *bpy_seq = NULL;
	
	if( !PyArg_ParseTuple( args, "O!", &Sequence_Type, &bpy_seq ) )
		return EXPP_ReturnPyObjError( PyExc_ValueError,
			"expects a sequence object" );
	
	/* quick way to tell if we dont have the seq */
	if (sce != bpy_seq->scene)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
			"Sequence does not exist here, cannot remove" );
	
	recurs_del_seq(&bpy_seq->seq->seqbase);
	del_seq__internal(bpy_seq->seq);
	clear_last_seq(); /* just incase */
	Py_RETURN_NONE;
}

static PyObject *Sequence_remove( BPy_Sequence * self, PyObject * args )
{
	return RemoveSeq_internal(&self->seq->seqbase, args, self->scene);
}

static PyObject *SceneSeq_remove( BPy_SceneSeq * self, PyObject * args )
{
	return RemoveSeq_internal( &((Editing *)self->scene->ed)->seqbase, args, self->scene);
}


static PyObject *Sequence_copy( BPy_Sequence * self )
{
	printf("Sequence Copy not implimented yet!\n");
	Py_RETURN_NONE;
}

/*****************************************************************************/
/* PythonTypeObject callback function prototypes			 */
/*****************************************************************************/
static void Sequence_dealloc( BPy_Sequence * obj );
static void SceneSeq_dealloc( BPy_Sequence * obj );
static PyObject *Sequence_repr( BPy_Sequence * obj );
static PyObject *SceneSeq_repr( BPy_SceneSeq * obj );
static int Sequence_compare( BPy_Sequence * a, BPy_Sequence * b );
static int SceneSeq_compare( BPy_SceneSeq * a, BPy_SceneSeq * b );

/*****************************************************************************/
/* Python BPy_Sequence methods:                                                  */
/*****************************************************************************/


static PyObject *Sequence_getIter( BPy_Sequence * self )
{
	Sequence *iter = self->seq->seqbase.first;
	
	if (!self->iter) {
		self->iter = iter;
		return EXPP_incr_ret ( (PyObject *) self );
	} else {
		return Sequence_CreatePyObject(self->seq, iter, self->scene);
	}
}

static PyObject *SceneSeq_getIter( BPy_SceneSeq * self )
{
	Sequence *iter = ((Editing *)self->scene->ed)->seqbase.first;
	
	if (!self->iter) {
		self->iter = iter;
		return EXPP_incr_ret ( (PyObject *) self );
	} else {
		return SceneSeq_CreatePyObject(self->scene, iter);
	}
}


/*
 * Return next Seq
 */
static PyObject *Sequence_nextIter( BPy_Sequence * self )
{
	PyObject *object;
	if( !(self->iter) ) {
		self->iter = NULL; /* so we can add objects again */
		return EXPP_ReturnPyObjError( PyExc_StopIteration,
				"iterator at end" );
	}
	
	object= Sequence_CreatePyObject( self->iter, NULL, self->scene ); 
	self->iter= self->iter->next;
	return object;
}


/*
 * Return next Seq
 */
static PyObject *SceneSeq_nextIter( BPy_Sequence * self )
{
	PyObject *object;
	if( !(self->iter) ) {
		self->iter = NULL; /* so we can add objects again */
		return EXPP_ReturnPyObjError( PyExc_StopIteration,
				"iterator at end" );
	}
	
	object= Sequence_CreatePyObject( self->iter, NULL, self->scene );
	self->iter= self->iter->next;
	return object;
}



static PyObject *Sequence_getName( BPy_Sequence * self )
{
	return PyString_FromString( self->seq->name+2 );
}

static int Sequence_setName( BPy_Sequence * self, PyObject * value )
{
	char *name = NULL;
	
	name = PyString_AsString ( value );
	if( !name )
		return EXPP_ReturnIntError( PyExc_TypeError,
					      "expected string argument" );

	strncpy(self->seq->name+2, name, 21);
	return 0;
}


static PyObject *Sequence_getSound( BPy_Sequence * self )
{
	if (self->seq->type == SEQ_RAM_SOUND && self->seq->sound)
		return Sound_CreatePyObject(self->seq->sound);
	Py_RETURN_NONE;
}

static PyObject *Sequence_getIpo( BPy_Sequence * self )
{
	struct Ipo *ipo;
	
	ipo = self->seq->ipo;

	if( ipo )
		return Ipo_CreatePyObject( ipo );
	Py_RETURN_NONE;
}


static PyObject *SceneSeq_getActive( BPy_SceneSeq * self )
{
	Sequence *last_seq = NULL, *seq;
	Editing *ed = self->scene->ed;

	if (!ed)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "scene has no sequence data to edit" );
	
	seq = ed->seqbasep->first;
	
	while (seq) {
		if (seq->flag & SELECT)
			last_seq = seq;
		
		seq = seq->next;
	}
	if (last_seq)
		return Sequence_CreatePyObject(last_seq, NULL, self->scene );
	
	Py_RETURN_NONE;
}

static PyObject *SceneSeq_getMetaStrip( BPy_SceneSeq * self )
{
	Sequence *seq = NULL;
	Editing *ed = self->scene->ed;
	MetaStack *ms;
	if (!ed)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "scene has no sequence data to edit" );
	
	ms = ed->metastack.last;
	if (!ms)
		Py_RETURN_NONE;
	
	seq = ms->parseq;
	return Sequence_CreatePyObject(seq, NULL, self->scene);
}


/*
 * this should accept a Py_None argument and just delete the Ipo link
 * (as Object_clearIpo() does)
 */

static int Sequence_setIpo( BPy_Sequence * self, PyObject * value )
{
	Ipo *ipo = NULL;
	Ipo *oldipo;
	ID *id;
	
	oldipo = self->seq->ipo;
	
	/* if parameter is not None, check for valid Ipo */

	if ( value != Py_None ) {
		if ( !Ipo_CheckPyObject( value ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
					"expected an Ipo object" );

		ipo = Ipo_FromPyObject( value );

		if( !ipo )
			return EXPP_ReturnIntError( PyExc_RuntimeError,
					"null ipo!" );

		if( ipo->blocktype != ID_SEQ )
			return EXPP_ReturnIntError( PyExc_TypeError,
					"Ipo is not a sequence data Ipo" );
	}

	/* if already linked to Ipo, delete link */

	if ( oldipo ) {
		id = &oldipo->id;
		if( id->us > 0 )
			id->us--;
	}

	/* assign new Ipo and increment user count, or set to NULL if deleting */

	self->seq->ipo = ipo;
	if ( ipo )
		id_us_plus(&ipo->id);

	return 0;
}

static PyObject *Sequence_getScene( BPy_Sequence * self )
{
	struct Scene *scene;
	
	scene = self->seq->scene;

	if( scene )
		return Scene_CreatePyObject( scene );
	Py_RETURN_NONE;
}


static PyObject *Sequence_getImages( BPy_Sequence * self )
{
	Strip *strip;
	StripElem *se;
	int i;
	PyObject *attr;
	
	if (self->seq->type != SEQ_IMAGE)
		return PyList_New(0);
			/*return EXPP_ReturnPyObjError( PyExc_TypeError,
					"Sequence is not an image type" );*/
	
	
	strip = self->seq->strip;
	se = strip->stripdata;
	attr = PyList_New(strip->len);
	
	for (i=0; i<strip->len; i++, se++) {
		PyList_SetItem( attr, i, PyString_FromString(se->name) );
	}

	return attr;
}



/*
 * get floating point attributes
 */
static PyObject *getIntAttr( BPy_Sequence *self, void *type )
{
	int param;
	struct Sequence *seq= self->seq;
	
	/*printf("%i %i %i %i %i %i %i %i %i\n", seq->len, seq->start, seq->startofs, seq->endofs, seq->startstill, seq->endstill, seq->startdisp, seq->enddisp, seq->depth );*/
	switch( (int)type ) {
	case EXPP_SEQ_ATTR_TYPE: 
		param = seq->type;
		break;
	case EXPP_SEQ_ATTR_CHAN:
		param = seq->machine;
		break;
	case EXPP_SEQ_ATTR_LENGTH:
		param = seq->len;
		break;
	case EXPP_SEQ_ATTR_START:
		param = seq->start;
		break;
	case EXPP_SEQ_ATTR_STARTOFS:
		param = seq->startofs;
		break;
	case EXPP_SEQ_ATTR_ENDOFS:
		param = seq->endofs;
		break;
	default:
		return EXPP_ReturnPyObjError( PyExc_RuntimeError, 
				"undefined type in getFloatAttr" );
	}

	return PyInt_FromLong( param );
}


/* internal functions for recursivly updating metastrip locatons */
static void intern_pos_update(Sequence * seq) {
	/* update startdisp and enddisp */
	seq->startdisp = seq->start + seq->startofs - seq->startstill;
	seq->enddisp = ((seq->start + seq->len) - seq->endofs )+ seq->endstill;
}

void intern_recursive_pos_update(Sequence * seq, int offset) {
	Sequence *iterseq;
	intern_pos_update(seq);
	if (seq->type != SEQ_META) return;
	
	for (iterseq = seq->seqbase.first; iterseq; iterseq= iterseq->next) {
		iterseq->start -= offset;
		intern_recursive_pos_update(iterseq, offset);
	}
}


static int setIntAttrClamp( BPy_Sequence *self, PyObject *value, void *type )
{
	struct Sequence *seq= self->seq;
	int number, origval=0;

	if( !PyInt_CheckExact ( value ) )
		return EXPP_ReturnIntError( PyExc_TypeError, "expected an int value" );
	
	number = PyInt_AS_LONG( value );
		
	switch( (int)type ) {
	case EXPP_SEQ_ATTR_CHAN:
		CLAMP(number, 1, 1024);
		seq->machine = number;
		break;
	case EXPP_SEQ_ATTR_START:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError( PyExc_RuntimeError,
				"cannot set the location of an effect directly" );
		CLAMP(number, -MAXFRAME, MAXFRAME);
		origval = seq->start;
		seq->start = number;
		break;
	
	case EXPP_SEQ_ATTR_STARTOFS:
		CLAMP(number, 0, seq->len - seq->endofs);
			return EXPP_ReturnIntError( PyExc_RuntimeError,
				"This property dosnt apply to an effect" );
		seq->startofs = number;
		break;
	case EXPP_SEQ_ATTR_ENDOFS:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError( PyExc_RuntimeError,
				"This property dosnt apply to an effect" );
		CLAMP(number, 0, seq->len - seq->startofs);
		seq->endofs = number;
		break;
	
	default:
		return EXPP_ReturnIntError( PyExc_RuntimeError,
				"undefined type in setFloatAttrClamp" );
	}
	
	intern_pos_update(seq);
	
	if ((int)type == EXPP_SEQ_ATTR_START && number != origval )
		intern_recursive_pos_update(seq, origval - seq->start);
	
	return 0;
}


static PyObject *getFlagAttr( BPy_Sequence *self, void *type )
{
	if (self->seq->flag & (int)type)
		Py_RETURN_TRUE;
	else
		Py_RETURN_FALSE;
}


/*
 * set floating point attributes which require clamping
 */

static int setFlagAttr( BPy_Sequence *self, PyObject *value, void *type )
{
	int t = (int)type;
	
	if (PyObject_IsTrue(value))
		self->seq->flag |= t;
	else {
		
		/* dont allow leftsel and rightsel when its not selected */
		if (t == SELECT)
			t = t + SEQ_LEFTSEL + SEQ_RIGHTSEL;
		
		self->seq->flag &= ~t;
	}
	return 0;
}


/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef BPy_Sequence_getseters[] = {
	{"name",
	 (getter)Sequence_getName, (setter)Sequence_setName,
	 "Sequence name",
	  NULL},
	{"ipo",
	 (getter)Sequence_getIpo, (setter)Sequence_setIpo,
	 "Sequence ipo",
	  NULL},

	{"scene",
	 (getter)Sequence_getScene, (setter)NULL,
	 "Sequence scene",
	  NULL},
	{"sound",
	 (getter)Sequence_getSound, (setter)NULL,
	 "Sequence name",
	  NULL},
	{"images",
	 (getter)Sequence_getImages, (setter)NULL,
	 "Sequence scene",
	  NULL},
	  
	{"type",
	 (getter)getIntAttr, (setter)NULL,
	 "",
	 (void *) EXPP_SEQ_ATTR_TYPE},
	{"channel",
	 (getter)getIntAttr, (setter)setIntAttrClamp,
	 "",
	 (void *) EXPP_SEQ_ATTR_CHAN},
	 
	{"length",
	 (getter)getIntAttr, (setter)setIntAttrClamp,
	 "",
	 (void *) EXPP_SEQ_ATTR_LENGTH},
	{"start",
	 (getter)getIntAttr, (setter)setIntAttrClamp,
	 "",
	 (void *) EXPP_SEQ_ATTR_START},
	{"startOffset",
	 (getter)getIntAttr, (setter)setIntAttrClamp,
	 "",
	 (void *) EXPP_SEQ_ATTR_STARTOFS},
	{"endOffset",
	 (getter)getIntAttr, (setter)setIntAttrClamp,
	 "",
	 (void *) EXPP_SEQ_ATTR_ENDOFS},

	{"sel",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "Sequence audio mute option",
	 (void *)SELECT},
	{"selLeft",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_LEFTSEL},
	{"selRight",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_RIGHTSEL},
	{"filtery",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_FILTERY},
	{"mute",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_MUTE},
	{"premul",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_MAKE_PREMUL},
	{"reversed",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_REVERSE_FRAMES},
	{"ipoLocked",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_IPO_FRAME_LOCKED},
	{"ipoLocked",
	 (getter)getFlagAttr, (setter)setFlagAttr,
	 "",
	 (void *)SEQ_IPO_FRAME_LOCKED},
	 
	{NULL,NULL,NULL,NULL,NULL}  /* Sentinel */
};

/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef BPy_SceneSeq_getseters[] = {
	{"active",
	 (getter)SceneSeq_getActive, (setter)NULL,
	 "the active strip",
	  NULL},
	{"metastrip",
	 (getter)SceneSeq_getMetaStrip, (setter)NULL,
	 "The currently active metastrip the user is editing",
	  NULL},
	{NULL,NULL,NULL,NULL,NULL}  /* Sentinel */
};

/*****************************************************************************/
/* Python TypeSequence structure definition:                                 */
/*****************************************************************************/
PyTypeObject Sequence_Type = {
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
	/*  For printing, in format "<module>.<name>" */
	"Blender Sequence",             /* char *tp_name; */
	sizeof( BPy_Sequence ),         /* int tp_basicsize; */
	0,                          /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	( destructor ) Sequence_dealloc,/* destructor tp_dealloc; */
	NULL,                       /* printfunc tp_print; */
	NULL,                       /* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	( cmpfunc ) Sequence_compare,   /* cmpfunc tp_compare; */
	( reprfunc ) Sequence_repr,     /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,                       /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,                       /* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	NULL,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	( getiterfunc ) Sequence_getIter,           /* getiterfunc tp_iter; */
	( iternextfunc ) Sequence_nextIter,           /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	BPy_Sequence_methods,           /* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	BPy_Sequence_getseters,         /* struct PyGetSetDef *tp_getset; */
	NULL,                       /* struct _typeobject *tp_base; */
	NULL,                       /* PyObject *tp_dict; */
	NULL,                       /* descrgetfunc tp_descr_get; */
	NULL,                       /* descrsetfunc tp_descr_set; */
	0,                          /* long tp_dictoffset; */
	NULL,                       /* initproc tp_init; */
	NULL,                       /* allocfunc tp_alloc; */
	NULL,                       /* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL,                       /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL,                       /* inquiry tp_is_gc;  */
	NULL,                       /* PyObject *tp_bases; */
	/* method resolution order */
	NULL,                       /* PyObject *tp_mro;  */
	NULL,                       /* PyObject *tp_cache; */
	NULL,                       /* PyObject *tp_subclasses; */
	NULL,                       /* PyObject *tp_weaklist; */
	NULL
};



/*****************************************************************************/
/* Python TypeSequence structure definition:                                 */
/*****************************************************************************/
PyTypeObject SceneSeq_Type = {
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
	/*  For printing, in format "<module>.<name>" */
	"Blender SceneSeq",             /* char *tp_name; */
	sizeof( BPy_Sequence ),         /* int tp_basicsize; */
	0,                          /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	( destructor ) SceneSeq_dealloc,/* destructor tp_dealloc; */
	NULL,                       /* printfunc tp_print; */
	NULL,                       /* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	( cmpfunc ) SceneSeq_compare,   /* cmpfunc tp_compare; */
	( reprfunc ) SceneSeq_repr,     /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,                       /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,                       /* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	NULL,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	( getiterfunc ) SceneSeq_getIter,           /* getiterfunc tp_iter; */
	( iternextfunc ) SceneSeq_nextIter,           /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	BPy_SceneSeq_methods,           /* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	BPy_SceneSeq_getseters,         /* struct PyGetSetDef *tp_getset; */
	NULL,                       /* struct _typeobject *tp_base; */
	NULL,                       /* PyObject *tp_dict; */
	NULL,                       /* descrgetfunc tp_descr_get; */
	NULL,                       /* descrsetfunc tp_descr_set; */
	0,                          /* long tp_dictoffset; */
	NULL,                       /* initproc tp_init; */
	NULL,                       /* allocfunc tp_alloc; */
	NULL,                       /* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL,                       /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL,                       /* inquiry tp_is_gc;  */
	NULL,                       /* PyObject *tp_bases; */
	/* method resolution order */
	NULL,                       /* PyObject *tp_mro;  */
	NULL,                       /* PyObject *tp_cache; */
	NULL,                       /* PyObject *tp_subclasses; */
	NULL,                       /* PyObject *tp_weaklist; */
	NULL
};


/*****************************************************************************/
/* Function:	  M_Sequence_Get						*/
/* Python equivalent:	  Blender.Sequence.Get				*/
/*****************************************************************************/
/*
PyObject *M_Sequence_Get( PyObject * self, PyObject * args )
{
	return SceneSeq_CreatePyObject( G.scene, NULL );
}
*/

/*****************************************************************************/
/* Function:	 initObject						*/
/*****************************************************************************/
PyObject *Sequence_Init( void )
{
	PyObject *submodule;
	if( PyType_Ready( &Sequence_Type ) < 0 )
		return NULL;
	if( PyType_Ready( &SceneSeq_Type ) < 0 )
		return NULL;
	
	/* NULL was M_Sequence_methods*/
	submodule = Py_InitModule3( "Blender.Scene.Sequence", NULL,
"The Blender Sequence module\n\n\
This module provides access to **Sequence Data** in Blender.\n" );

	/*Add SUBMODULES to the module*/
	/*PyDict_SetItemString(dict, "Constraint", Constraint_Init()); //creates a *new* module*/
	return submodule;
}


/*****************************************************************************/
/* Function:	Sequence_CreatePyObject					 */
/* Description: This function will create a new BlenObject from an existing  */
/*		Object structure.					 */
/*****************************************************************************/
PyObject *Sequence_CreatePyObject( struct Sequence * seq, struct Sequence * iter, struct Scene *sce)
{
	BPy_Sequence *pyseq;

	if( !seq )
		Py_RETURN_NONE;

	pyseq =
		( BPy_Sequence * ) PyObject_NEW( BPy_Sequence, &Sequence_Type );

	if( pyseq == NULL ) {
		return ( NULL );
	}
	pyseq->seq = seq;
	pyseq->iter = iter;
	pyseq->scene = sce;
	
	return ( ( PyObject * ) pyseq );
}

/*****************************************************************************/
/* Function:	SceneSeq_CreatePyObject					 */
/* Description: This function will create a new BlenObject from an existing  */
/*		Object structure.					 */
/*****************************************************************************/
PyObject *SceneSeq_CreatePyObject( struct Scene * scn, struct Sequence * iter)
{
	BPy_SceneSeq *pysceseq;

	if( !scn )
		Py_RETURN_NONE;

	pysceseq =
		( BPy_SceneSeq * ) PyObject_NEW( BPy_SceneSeq, &SceneSeq_Type );

	if( pysceseq == NULL ) {
		return ( NULL );
	}
	pysceseq->scene = scn;
	pysceseq->iter = iter;
	
	return ( ( PyObject * ) pysceseq );
}


/*****************************************************************************/
/* Function:	Sequence_CheckPyObject					 */
/* Description: This function returns true when the given PyObject is of the */
/*		type Sequence. Otherwise it will return false.		 */
/*****************************************************************************/
int Sequence_CheckPyObject( PyObject * py_seq)
{
	return ( py_seq->ob_type == &Sequence_Type );
}
int SceneSeq_CheckPyObject( PyObject * py_seq)
{
	return ( py_seq->ob_type == &SceneSeq_Type );
}

/*****************************************************************************/
/* Function:	Sequence_FromPyObject					 */
/* Description: This function returns the Blender sequence from the given	 */
/*		PyObject.						 */
/*****************************************************************************/
struct Sequence *Sequence_FromPyObject( PyObject * py_seq )
{
	BPy_Sequence *blen_seq;

	blen_seq = ( BPy_Sequence * ) py_seq;
	return ( blen_seq->seq );
}

/*****************************************************************************/
/* Function:	Sequence_dealloc						 */
/* Description: This is a callback function for the BlenObject type. It is  */
/*		the destructor function.				 */
/*****************************************************************************/
static void Sequence_dealloc( BPy_Sequence * seq )
{
	PyObject_DEL( seq );
}
static void SceneSeq_dealloc( BPy_Sequence * seq )
{
	PyObject_DEL( seq );
}


/*****************************************************************************/
/* Function:	Sequence_compare						 */
/* Description: This is a callback function for the BPy_Sequence type. It	 */
/*		compares two Sequence_Type objects. Only the "==" and "!="  */
/*		comparisons are meaninful. Returns 0 for equality and -1 if  */
/*		they don't point to the same Blender Object struct.	 */
/*		In Python it becomes 1 if they are equal, 0 otherwise.	 */
/*****************************************************************************/
static int Sequence_compare( BPy_Sequence * a, BPy_Sequence * b )
{
	Sequence *pa = a->seq, *pb = b->seq;
	return ( pa == pb ) ? 0 : -1;
}

static int SceneSeq_compare( BPy_SceneSeq * a, BPy_SceneSeq * b )
{
	
	Scene *pa = a->scene, *pb = b->scene;
	return ( pa == pb ) ? 0 : -1;
}

/*****************************************************************************/
/* Function:	Sequence_repr / SceneSeq_repr						 */
/* Description: This is a callback function for the BPy_Sequence type. It	 */
/*		builds a meaninful string to represent object objects.	 */
/*****************************************************************************/
static PyObject *Sequence_repr( BPy_Sequence * self )
{
	return PyString_FromFormat( "[Sequence Strip \"%s\"]",
					self->seq->name + 2 );
}
static PyObject *SceneSeq_repr( BPy_SceneSeq * self )
{
	return PyString_FromFormat( "[Scene Sequence \"%s\"]",
				self->scene->id.name + 2 );
}

