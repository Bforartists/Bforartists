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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "sceneSequence.h" /* This must come first */

#include "MEM_guardedalloc.h"

#include "DNA_sequence_types.h"
#include "DNA_scene_types.h" /* for Base */

#include "BKE_mesh.h"
#include "BKE_image.h" // RFS: openanim
#include "BKE_library.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_scene.h"

#include "BIF_editseq.h" /* get_last_seq */
#include "BIF_editsound.h" // RFS: sound_open_hdaudio
#include "BLI_blenlib.h"
#include "BSE_sequence.h"
#include "BSE_seqeffects.h"
#include "Ipo.h"
#include "blendef.h"  /* CLAMP */
#include "BKE_utildefines.h"
#include "Scene.h"
#include "Sound.h"
#include "gen_utils.h"

#include "IMB_imbuf_types.h" // RFS: IB_rect
#include "IMB_imbuf.h" // RFS: IMB_anim_get_duration

enum seq_consts
{
	EXPP_SEQ_ATTR_TYPE = 0,
	EXPP_SEQ_ATTR_CHAN,
	EXPP_SEQ_ATTR_LENGTH,
	EXPP_SEQ_ATTR_START,
	EXPP_SEQ_ATTR_STARTOFS,
	EXPP_SEQ_ATTR_ENDOFS,
	EXPP_SEQ_ATTR_STARTSTILL,
	EXPP_SEQ_ATTR_ENDSTILL,
	EXPP_SEQ_ATTR_STARTDISP,
	EXPP_SEQ_ATTR_ENDDISP
};

enum seq_effect_consts
{
		/* speed  */
	EXPP_SEQ_ATTR_EFFECT_GLOBAL_SPEED,
	EXPP_SEQ_ATTR_EFFECT_IPO_IS_VELOCITY,
	EXPP_SEQ_ATTR_EFFECT_FRAME_BLENDING,
	EXPP_SEQ_ATTR_EFFECT_NORMALIZE_IPO_0_1,

		/* wipe */
	EXPP_SEQ_ATTR_EFFECT_ANGLE,
	EXPP_SEQ_ATTR_EFFECT_BLUR,
	EXPP_SEQ_ATTR_EFFECT_WIPE_IN
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
static PyObject *Sequence_copy(BPy_Sequence * self);
static PyObject *Sequence_update(BPy_Sequence * self, PyObject *args);
static PyObject *Sequence_new(BPy_Sequence * self, PyObject * args);
static PyObject *Sequence_remove(BPy_Sequence * self, PyObject * args);
static PyObject *Sequence_rebuildProxy(BPy_Sequence * self);

static PyObject *SceneSeq_new(BPy_SceneSeq * self, PyObject * args);
static PyObject *SceneSeq_remove(BPy_SceneSeq * self, PyObject * args);
static void intern_pos_update(Sequence * seq);

static PyMethodDef BPy_Sequence_methods[] = {
	/* name, method, flags, doc */
	{"new", (PyCFunction) Sequence_new, METH_VARARGS,
		"(data) - Return a new sequence."},
	{"remove", (PyCFunction) Sequence_remove, METH_VARARGS,
		"(data) - Remove a strip."},
	{"__copy__", (PyCFunction) Sequence_copy, METH_NOARGS,
		"() - Return a copy of the sequence containing the same objects."},
	{"copy", (PyCFunction) Sequence_copy, METH_NOARGS,
		"() - Return a copy of the sequence containing the same objects."},
	{"update", (PyCFunction) Sequence_update, METH_VARARGS,
		"() - Force and update of the sequence strip"},
	{"rebuildProxy", (PyCFunction) Sequence_rebuildProxy, METH_VARARGS,
		"() - Rebuild the active strip's Proxy."},
	{NULL, NULL, 0, NULL}
};

static PyMethodDef BPy_SceneSeq_methods[] = {
	/* name, method, flags, doc */
	{"new", (PyCFunction) SceneSeq_new, METH_VARARGS,
		"(data) - Return a new sequence."},
	{"remove", (PyCFunction) SceneSeq_remove, METH_VARARGS,
		"(data) - Remove a strip."},
	{NULL, NULL, 0, NULL}
};

/* use to add a sequence to a scene or its listbase */
static PyObject *NewSeq_internal(ListBase *seqbase, PyObject * args, Scene *sce)
{
	PyObject *py_data = NULL;

	Sequence *seq;
	PyObject *pyob1 = NULL, *pyob2 = NULL, *pyob3 = NULL; /* for effects */
	int type;

	int a;
	Strip *strip;
	StripElem *se;
	int start, machine;

	if (!PyArg_ParseTuple(args, "Oii", &py_data, &start, &machine))
		return EXPP_ReturnPyObjError(PyExc_ValueError,
									"expect sequence data then 2 ints - (seqdata, start, track)");

	if (machine < 1 || machine >= MAXSEQ)
	{
		return EXPP_ReturnPyObjError(PyExc_ValueError,
									"track out of range");
	}

	seq = alloc_sequence(seqbase, start, machine); /* warning, this sets last */


	if (PyList_Check(py_data)) /* new metastrip, list of seqs */
	{
		/* Warning, no checks for audio which should not be allowed, or a blank metaseq if an empty list */
		int fail= 0;
		Sequence *seq_iter;
		PyObject *item;
		seq->type= SEQ_META;


		for(a=PyList_GET_SIZE(py_data)-1; a >= 0; a--) {
			item= PyList_GET_ITEM(py_data, a);
			if (!BPy_Sequence_Check(item)) { /* ignore non seq types */
				fail= 1;
				break;
			}

			seq_iter = ((BPy_Sequence *) item)->seq;
			if (BLI_findindex(seqbase, seq_iter) == -1) {
				fail= 2;
				break;
			}
		}

		if (fail) {
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			if (fail==1)
				return EXPP_ReturnPyObjError(PyExc_ValueError, "One of more of the list items was not a sequence strip");
			else
				return EXPP_ReturnPyObjError(PyExc_ValueError, "One of more of the list items sequence strips is not in this meta or scene");
		}


		for(a=PyList_GET_SIZE(py_data)-1; a >= 0; a--) {
			item= PyList_GET_ITEM(py_data, a);
			seq_iter = ((BPy_Sequence *) item)->seq;
			BLI_remlink(seqbase, seq_iter);
			BLI_addtail(&seq->seqbase, seq_iter);
		}

		clear_last_seq(); /* just incase */
		calc_sequence(seq);

		seq->strip= MEM_callocN(sizeof(Strip), "metastrip");
		seq->strip->len= seq->len;
		seq->strip->us= 1;
	}
	else if (PyTuple_Check(py_data) && PyTuple_GET_SIZE(py_data) >= 2 && BPy_Sequence_Check(PyTuple_GET_ITEM(py_data, 1)))
	{

		struct SeqEffectHandle sh;
		Sequence *seq1, *seq2 = NULL, *seq3 = NULL; /* for effects */

		if (!PyArg_ParseTuple(py_data, "iO!|O!O!", &type, &Sequence_Type, &pyob1, &Sequence_Type, &pyob2, &Sequence_Type, &pyob3))
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"effect stripts expected an effect type int and 1 to 3 sequence strips");
		}


		seq1 = ((BPy_Sequence *) pyob1)->seq;
		if (pyob2) seq2 = ((BPy_Sequence *) pyob2)->seq;
		if (pyob3) seq3 = ((BPy_Sequence *) pyob3)->seq;

		if (type <= SEQ_EFFECT || type > SEQ_EFFECT_MAX || type == SEQ_PLUGIN)
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"sequencer type out of range, expected a value from 9 to 29, plugins not supported");
		}


		if (BLI_findindex(seqbase, seq1) == -1 || (seq2 && BLI_findindex(seqbase, seq2) == -1) || (seq3 && BLI_findindex(seqbase, seq3) == -1))
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"one of the given effect sequences wasnt in accessible at the same level as the sequence being added");
		}

		if ((seq2 && seq2 == seq1) || (seq3 && (seq3 == seq1 || seq3 == seq2)))
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"2 or more of the sequence arguments were the same");

		}

		/* allocate and initialize */
		seq->type = type;

		sh = get_sequence_effect(seq);

		seq->seq1 = seq1;
		seq->seq2 = seq2;
		seq->seq3 = seq3;

		sh.init(seq);

		if (!seq1)
		{
			seq->len = 1;
			seq->startstill = 25;
			seq->endstill = 24;
		}

		calc_sequence(seq);

		seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
		strip->len = seq->len;
		strip->us = 1;
		if (seq->len > 0)
			strip->stripdata = MEM_callocN(seq->len * sizeof (StripElem), "stripelem");

#if 0
		/* initialize plugin */
		if (newseq->type == SEQ_PLUGIN)
		{
			sh.init_plugin(seq, str);

			if (newseq->plugin == 0)
			{
				BLI_remlink(ed->seqbasep, seq);
				free_sequence(seq);
				return 0;
			}
		}
#endif

		update_changed_seq_and_deps(seq, 1, 1);

	}
	else if (PyTuple_Check(py_data) && PyTuple_GET_SIZE(py_data) == 2)
	{
		/* Image */
		PyObject *list;
		char *name;

		if (!PyArg_ParseTuple(py_data, "sO!", &name, &PyList_Type, &list))
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"images data needs to be a tuple of a string and a list of images - (path, [filenames...])");
		}

		seq->type = SEQ_IMAGE;

		seq->len = PyList_Size(list);

		/* strip and stripdata */
		seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
		strip->len = seq->len;
		strip->us = 1;
		strncpy(strip->dir, name, FILE_MAXDIR - 1);
		strip->stripdata = se = MEM_callocN(seq->len * sizeof (StripElem), "stripelem");

		for (a = 0; a < seq->len; a++)
		{
			name = PyString_AsString(PyList_GetItem(list, a));
			strncpy(se->name, name, FILE_MAXFILE - 1);
			se++;
		}
	}
	else if (PyTuple_Check(py_data) && PyTuple_GET_SIZE(py_data) == 3)
	{
		float r, g, b;
		SolidColorVars *colvars;

		if (!PyArg_ParseTuple(py_data, "fff", &r, &g, &b))
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);
			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"color needs to be a tuple of 3 floats - (r,g,b)");
		}

		seq->effectdata = MEM_callocN(sizeof (struct SolidColorVars), "solidcolor");
		colvars = (SolidColorVars *) seq->effectdata;

		seq->type = SEQ_COLOR;

		CLAMP(r, 0, 1);
		CLAMP(g, 0, 1);
		CLAMP(b, 0, 1);

		colvars->col[0] = r;
		colvars->col[1] = b;
		colvars->col[2] = g;

		/* basic defaults */
		seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
		strip->len = seq->len = 1;
		strip->us = 1;
		strip->stripdata = se = MEM_callocN(seq->len * sizeof (StripElem), "stripelem");

	}
	else if (PyTuple_Check(py_data) && PyTuple_GET_SIZE(py_data) == 4)
	{
		// MOVIE or AUDIO_HD
		char *filename;
		char *dir;
		char *fullpath;
		char *type;
		int totframe;

		if (!PyArg_ParseTuple(py_data, "ssss", &filename, &dir, &fullpath, &type))
		{
			BLI_remlink(seqbase, seq);
			free_sequence(seq);

			return EXPP_ReturnPyObjError(PyExc_ValueError,
										"movie/audio hd data needs to be a tuple of a string and a list of images - (filename, dir, fullpath, type)");
		}

		// RFS - Attempting to support Movie and Audio (HD) strips
#define RFS
#ifdef RFS
		// Movie strips
		if (strcmp(type, "movie") == 0)
		{
			/* open it as an animation */
			struct anim * an = openanim(fullpath, IB_rect);
			if (an == 0)
			{
				BLI_remlink(seqbase, seq);
				free_sequence(seq);

				return EXPP_ReturnPyObjError(PyExc_ValueError,
											"invalid movie strip");
			}

			/* get the length in frames */
			totframe = IMB_anim_get_duration(an);

			/* set up sequence */
			seq->type = SEQ_MOVIE;
			seq->len = totframe;
			seq->anim = an;
			seq->anim_preseek = IMB_anim_get_preseek(an);

			calc_sequence(seq);

			/* strip and stripdata */
			seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
			strip->len = totframe;
			strip->us = 1;
			strncpy(strip->dir, dir, FILE_MAXDIR - 1); // ????
			strip->stripdata = se = MEM_callocN(sizeof (StripElem), "stripelem");

			/* name movie in first strip */
			strncpy(se->name, filename, FILE_MAXFILE - 1); // ????
		}

		// Audio (HD) strips
		if (strcmp(type, "audio_hd") == 0)
		{
			struct hdaudio *hdaudio;

			totframe = 0;

			/* is it a sound file? */
			hdaudio = sound_open_hdaudio(fullpath);
			if (hdaudio == 0)
			{
				BLI_remlink(seqbase, seq);
				free_sequence(seq);

				return EXPP_ReturnPyObjError(PyExc_ValueError,
											fullpath);
			}

			totframe = sound_hdaudio_get_duration(hdaudio, FPS);

			/* set up sequence */
			seq->type = SEQ_HD_SOUND;
			seq->len = totframe;
			seq->hdaudio = hdaudio;

			calc_sequence(seq);

			/* strip and stripdata - same as for MOVIE */
			seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
			strip->len = totframe;
			strip->us = 1;
			strncpy(strip->dir, dir, FILE_MAXDIR - 1); // ????
			strip->stripdata = se = MEM_callocN(sizeof (StripElem), "stripelem");

			/* name movie in first strip */
			strncpy(se->name, filename, FILE_MAXFILE - 1); // ????
		}
#endif

	}
	else if (BPy_Sound_Check(py_data))
	{
		/* RAM sound */
		int totframe;
		bSound *sound = ((BPy_Sound *) py_data)->sound;

		seq->type = SEQ_RAM_SOUND;
		seq->sound = sound;

		totframe = (int) (((float) (sound->streamlen - 1) / ((float) sce->audio.mixrate * 4.0))* (float) sce->r.frs_sec / sce->r.frs_sec_base);

		sound->flags |= SOUND_FLAGS_SEQUENCE;

		/* strip and stripdata */
		seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
		strip->len = totframe;
		strip->us = 1;
		strncpy(strip->dir, sound->name, FILE_MAXDIR - 1);
		strip->stripdata = se = MEM_callocN(sizeof (StripElem), "stripelem");

		/* name sound in first strip */
		strncpy(se->name, sound->name, FILE_MAXFILE - 1);

	}
	else if (BPy_Scene_Check(py_data))
	{
		/* scene */
		Scene *sceseq = ((BPy_Scene *) py_data)->scene;

		seq->type = SEQ_SCENE;
		seq->scene = sceseq;

		/*seq->sfra= sce->r.sfra;*/
		seq->len = sceseq->r.efra - sceseq->r.sfra + 1;

		seq->strip = strip = MEM_callocN(sizeof (Strip), "strip");
		strncpy(seq->name + 2, sceseq->id.name + 2,
				sizeof (seq->name) - 2);
		strip->len = seq->len;
		strip->us = 1;
	}
	else
	{
		// RFS: REMOVED MOVIE FROM HERE
	}
	strncpy(seq->name + 2, "Untitled", 21);
	intern_pos_update(seq);
	return Sequence_CreatePyObject(seq, NULL, sce);
}

static PyObject *Sequence_new(BPy_Sequence * self, PyObject * args)
{
	return NewSeq_internal(&self->seq->seqbase, args, self->scene);
}

static PyObject *SceneSeq_new(BPy_SceneSeq * self, PyObject * args)
{
	return NewSeq_internal(&((Editing *) self->scene->ed)->seqbase, args, self->scene);
}

static void del_seq__internal(Sequence *seq)
{
	if (seq->ipo) seq->ipo->id.us--;

	if (seq->type == SEQ_RAM_SOUND && seq->sound)
		seq->sound->id.us--;
	free_sequence(seq);
}

static void recurs_del_seq(ListBase *lb)
{
	Sequence *seq, *seqn;

	seq = lb->first;
	while (seq)
	{
		seqn = seq->next;
		BLI_remlink(lb, seq);
		if (seq->type == SEQ_META) recurs_del_seq(&seq->seqbase);
		del_seq__internal(seq);
		seq = seqn;
	}
}

static PyObject *RemoveSeq_internal(ListBase *seqbase, PyObject * args, Scene *sce)
{
	BPy_Sequence *bpy_seq = NULL;

	if (!PyArg_ParseTuple(args, "O!", &Sequence_Type, &bpy_seq))
		return EXPP_ReturnPyObjError(PyExc_ValueError,
									"expects a sequence object");

	/* quick way to tell if we dont have the seq */
	if (sce != bpy_seq->scene)
		return EXPP_ReturnPyObjError(PyExc_RuntimeError,
									"Sequence does not exist here, cannot remove");

	recurs_del_seq(&bpy_seq->seq->seqbase);
	del_seq__internal(bpy_seq->seq);
	clear_last_seq(); /* just incase */
	Py_RETURN_NONE;
}

static PyObject *Sequence_remove(BPy_Sequence * self, PyObject * args)
{
	return RemoveSeq_internal(&self->seq->seqbase, args, self->scene);
}

static PyObject *SceneSeq_remove(BPy_SceneSeq * self, PyObject * args)
{
	return RemoveSeq_internal(&((Editing *) self->scene->ed)->seqbase, args, self->scene);
}

static PyObject *Sequence_copy(BPy_Sequence * self)
{
	printf("Sequence Copy not implimented yet!\n");
	Py_RETURN_NONE;
}

static PyObject *Sequence_update(BPy_Sequence * self, PyObject *args)
{
	int data= 0;
	if (!PyArg_ParseTuple(args, "|i:update", &data))
		return NULL; 				

	if (data) {
		update_changed_seq_and_deps(self->seq, 1, 1);
		new_tstripdata(self->seq);
	}
	calc_sequence(self->seq);
	calc_sequence_disp(self->seq);
	Py_RETURN_NONE;
}


/*****************************************************************************/
/* PythonTypeObject callback function prototypes			 */
/*****************************************************************************/
static PyObject *Sequence_repr(BPy_Sequence * obj);
static PyObject *SceneSeq_repr(BPy_SceneSeq * obj);
static int Sequence_compare(BPy_Sequence * a, BPy_Sequence * b);
static int SceneSeq_compare(BPy_SceneSeq * a, BPy_SceneSeq * b);

/*****************************************************************************/
/* Python BPy_Sequence methods:                                                  */

/*****************************************************************************/


static PyObject *Sequence_getIter(BPy_Sequence * self)
{
	Sequence *iter = self->seq->seqbase.first;

	if (!self->iter)
	{
		self->iter = iter;
		return EXPP_incr_ret((PyObject *) self);
	}
	else
	{
		return Sequence_CreatePyObject(self->seq, iter, self->scene);
	}
}

static PyObject *SceneSeq_getIter(BPy_SceneSeq * self)
{
	Sequence *iter = ((Editing *) self->scene->ed)->seqbase.first;

	if (!self->iter)
	{
		self->iter = iter;
		return EXPP_incr_ret((PyObject *) self);
	}
	else
	{
		return SceneSeq_CreatePyObject(self->scene, iter);
	}
}

/*
 * Return next Seq
 */
static PyObject *Sequence_nextIter(BPy_Sequence * self)
{
	PyObject *object;
	if (!(self->iter))
	{
		self->iter = NULL; /* so we can add objects again */
		return EXPP_ReturnPyObjError(PyExc_StopIteration,
									"iterator at end");
	}

	object = Sequence_CreatePyObject(self->iter, NULL, self->scene);
	self->iter = self->iter->next;
	return object;
}

/*
 * Return next Seq
 */
static PyObject *SceneSeq_nextIter(BPy_Sequence * self)
{
	PyObject *object;
	if (!(self->iter))
	{
		self->iter = NULL; /* so we can add objects again */
		return EXPP_ReturnPyObjError(PyExc_StopIteration,
									"iterator at end");
	}

	object = Sequence_CreatePyObject(self->iter, NULL, self->scene);
	self->iter = self->iter->next;
	return object;
}

static PyObject *Sequence_getName(BPy_Sequence * self)
{
	return PyString_FromString(self->seq->name + 2);
}

static int Sequence_setName(BPy_Sequence * self, PyObject * value)
{
	char *name = NULL;

	name = PyString_AsString(value);
	if (!name)
		return EXPP_ReturnIntError(PyExc_TypeError,
								"expected string argument");

	strncpy(self->seq->name + 2, name, 21);
	return 0;
}

static PyObject *Sequence_getProxyDir(BPy_Sequence * self)
{
	return PyString_FromString(self->seq->strip->proxy ? self->seq->strip->proxy->dir : "");
}

static int Sequence_setProxyDir(BPy_Sequence * self, PyObject * value)
{
	char *name = NULL;

	name = PyString_AsString(value);
	if (!name)
	{
		return EXPP_ReturnIntError(PyExc_TypeError,
								"expected string argument");
	}

	if (strlen(name) == 0)
	{
		if (self->seq->strip->proxy)
		{
			MEM_freeN(self->seq->strip->proxy);
		}
	}
	else
	{
		self->seq->strip->proxy = MEM_callocN(sizeof (struct StripProxy), "StripProxy");
		strncpy(self->seq->strip->proxy->dir, name, 160);
	}
	return 0;
}

static PyObject *Sequence_rebuildProxy(BPy_Sequence * self)
{
	if (self->seq->strip->proxy)
		seq_proxy_rebuild(self->seq);
	Py_RETURN_NONE;
}

static PyObject *Sequence_getSound(BPy_Sequence * self)
{
	if (self->seq->type == SEQ_RAM_SOUND && self->seq->sound)
		return Sound_CreatePyObject(self->seq->sound);
	Py_RETURN_NONE;
}

static PyObject *Sequence_getIpo(BPy_Sequence * self)
{
	struct Ipo *ipo;

	ipo = self->seq->ipo;

	if (ipo)
		return Ipo_CreatePyObject(ipo);
	Py_RETURN_NONE;
}

static PyObject *SceneSeq_getActive(BPy_SceneSeq * self)
{
	Sequence *last_seq = NULL, *seq;
	Editing *ed = self->scene->ed;

	if (!ed)
		return EXPP_ReturnPyObjError(PyExc_RuntimeError,
									"scene has no sequence data to edit");

	seq = ed->seqbasep->first;

	while (seq)
	{
		if (seq->flag & SELECT)
			last_seq = seq;

		seq = seq->next;
	}
	if (last_seq)
		return Sequence_CreatePyObject(last_seq, NULL, self->scene);

	Py_RETURN_NONE;
}

static PyObject *SceneSeq_getMetaStrip(BPy_SceneSeq * self)
{
	Sequence *seq = NULL;
	Editing *ed = self->scene->ed;
	MetaStack *ms;
	if (!ed)
		return EXPP_ReturnPyObjError(PyExc_RuntimeError,
									"scene has no sequence data to edit");

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

static int Sequence_setIpo(BPy_Sequence * self, PyObject * value)
{
	Ipo *ipo = NULL;
	Ipo *oldipo;
	ID *id;

	oldipo = self->seq->ipo;

	/* if parameter is not None, check for valid Ipo */

	if (value != Py_None)
	{
		if (!BPy_Ipo_Check(value))
			return EXPP_ReturnIntError(PyExc_TypeError,
									"expected an Ipo object");

		ipo = Ipo_FromPyObject(value);

		if (!ipo)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"null ipo!");

		if (ipo->blocktype != ID_SEQ)
			return EXPP_ReturnIntError(PyExc_TypeError,
									"Ipo is not a sequence data Ipo");
	}

	/* if already linked to Ipo, delete link */

	if (oldipo)
	{
		id = &oldipo->id;
		if (id->us > 0)
			id->us--;
	}

	/* assign new Ipo and increment user count, or set to NULL if deleting */

	self->seq->ipo = ipo;
	if (ipo)
		id_us_plus(&ipo->id);

	return 0;
}

static PyObject *Sequence_getScene(BPy_Sequence * self)
{
	struct Scene *scene;

	scene = self->seq->scene;

	if (scene)
		return Scene_CreatePyObject(scene);
	Py_RETURN_NONE;
}

static PyObject *Sequence_getImages(BPy_Sequence * self)
{
	Strip *strip;
	StripElem *se;
	int i;
	PyObject *list, *ret;

	if (self->seq->type != SEQ_IMAGE)
	{
		list = PyList_New(0);
		ret = Py_BuildValue("sO", "", list);
		Py_DECREF(list);
		return ret;
	}

	/*return EXPP_ReturnPyObjError( PyExc_TypeError,
			"Sequence is not an image type" );*/


	strip = self->seq->strip;
	se = strip->stripdata;
	list = PyList_New(strip->len);

	for (i = 0; i < strip->len; i++, se++)
	{
		PyList_SetItem(list, i, PyString_FromString(se->name));
	}

	ret = Py_BuildValue("sO", strip->dir, list);
	Py_DECREF(list);
	return ret;
}

static int Sequence_setImages(BPy_Sequence * self, PyObject *value)
{
	Strip *strip;
	StripElem *se;
	int i;
	PyObject *list;
	char *basepath, *name;

	if (self->seq->type != SEQ_IMAGE)
	{
		return EXPP_ReturnIntError(PyExc_TypeError,
								"Sequence is not an image type");
	}

	if (!PyArg_ParseTuple
		(value, "sO!", &basepath, &PyList_Type, &list))
		return EXPP_ReturnIntError(PyExc_TypeError,
								"expected string and optional list argument");

	strip = self->seq->strip;
	se = strip->stripdata;

	/* for now dont support different image list sizes */
	if (PyList_Size(list) != strip->len)
	{
		return EXPP_ReturnIntError(PyExc_TypeError,
								"at the moment only image lista with the same number of images as the strip are supported");
	}

	strncpy(strip->dir, basepath, sizeof (strip->dir));

	for (i = 0; i < strip->len; i++, se++)
	{
		name = PyString_AsString(PyList_GetItem(list, i));
		if (name)
		{
			strncpy(se->name, name, sizeof (se->name));
		}
		else
		{
			PyErr_Clear();
		}
	}

	return 0;
}

static PyObject *M_Sequence_BlendModesDict(void)
{
	PyObject *M = PyConstant_New();

	if (M)
	{
		BPy_constant *d = (BPy_constant *) M;
		PyConstant_Insert(d, "CROSS", PyInt_FromLong(SEQ_CROSS));
		PyConstant_Insert(d, "ADD", PyInt_FromLong(SEQ_ADD));
		PyConstant_Insert(d, "SUBTRACT", PyInt_FromLong(SEQ_SUB));
		PyConstant_Insert(d, "ALPHAOVER", PyInt_FromLong(SEQ_ALPHAOVER));
		PyConstant_Insert(d, "ALPHAUNDER", PyInt_FromLong(SEQ_ALPHAUNDER));
		PyConstant_Insert(d, "GAMMACROSS", PyInt_FromLong(SEQ_GAMCROSS));
		PyConstant_Insert(d, "MULTIPLY", PyInt_FromLong(SEQ_MUL));
		PyConstant_Insert(d, "OVERDROP", PyInt_FromLong(SEQ_OVERDROP));
		PyConstant_Insert(d, "PLUGIN", PyInt_FromLong(SEQ_PLUGIN));
		PyConstant_Insert(d, "WIPE", PyInt_FromLong(SEQ_WIPE));
		PyConstant_Insert(d, "GLOW", PyInt_FromLong(SEQ_GLOW));
		PyConstant_Insert(d, "TRANSFORM", PyInt_FromLong(SEQ_TRANSFORM));
		PyConstant_Insert(d, "COLOR", PyInt_FromLong(SEQ_COLOR));
		PyConstant_Insert(d, "SPEED", PyInt_FromLong(SEQ_SPEED));
	}
	return M;
}

static PyObject *Sequence_getBlendMode(BPy_Sequence * self)
{
	return PyInt_FromLong(self->seq->blend_mode);
}

static int Sequence_setBlendMode(BPy_Sequence * self, PyObject * value)
{
	struct Sequence *seq = self->seq;
	int number = PyInt_AsLong(value);

	if (number == -1 && PyErr_Occurred())
		return EXPP_ReturnIntError(PyExc_TypeError, "expected an int value");

	if (!seq_can_blend(seq))
		return EXPP_ReturnIntError(PyExc_AttributeError, "this sequence type dosnt support blending");

	if (number < SEQ_EFFECT || number > SEQ_EFFECT_MAX)
		return EXPP_ReturnIntError(PyExc_TypeError, "expected an int value");

	seq->blend_mode = number;

	return 0;
}

/*
 * get floating point attributes
 */
static PyObject *getIntAttr(BPy_Sequence *self, void *type)
{
	int param;
	struct Sequence *seq = self->seq;

	/*printf("%i %i %i %i %i %i %i %i %i\n", seq->len, seq->start, seq->startofs, seq->endofs, seq->startstill, seq->endstill, seq->startdisp, seq->enddisp, seq->depth );*/
	switch (GET_INT_FROM_POINTER(type))
	{
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
	case EXPP_SEQ_ATTR_STARTSTILL:
		param = seq->startstill;
		break;
	case EXPP_SEQ_ATTR_ENDSTILL:
		param = seq->endstill;
		break;
	case EXPP_SEQ_ATTR_STARTDISP:
		param = seq->startdisp;
		break;
	case EXPP_SEQ_ATTR_ENDDISP:
		param = seq->enddisp;
		break;
	default:
		return EXPP_ReturnPyObjError(PyExc_RuntimeError,
									"undefined type in getIntAttr");
	}

	return PyInt_FromLong(param);
}

/* internal functions for recursivly updating metastrip locatons */
static void intern_pos_update(Sequence * seq)
{
	/* update startdisp and enddisp */
	calc_sequence_disp(seq);
}

void intern_recursive_pos_update(Sequence * seq, int offset)
{
	Sequence *iterseq;
	intern_pos_update(seq);
	if (seq->type != SEQ_META) return;

	for (iterseq = seq->seqbase.first; iterseq; iterseq = iterseq->next)
	{
		iterseq->start -= offset;
		intern_recursive_pos_update(iterseq, offset);
	}
}

static int setIntAttrClamp(BPy_Sequence *self, PyObject *value, void *type)
{
	struct Sequence *seq = self->seq;
	int number, origval = 0, regen_data;

	if (!PyInt_Check(value))
		return EXPP_ReturnIntError(PyExc_TypeError, "expected an int value");

	number = PyInt_AS_LONG(value);

	switch (GET_INT_FROM_POINTER(type))
	{
	case EXPP_SEQ_ATTR_CHAN:
		CLAMP(number, 1, 1024);
		seq->machine = number;
		regen_data = 0;
		break;
	case EXPP_SEQ_ATTR_START:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"cannot set the location of an effect directly");
		CLAMP(number, -MAXFRAME, MAXFRAME);
		origval = seq->start;
		seq->start = number;
		regen_data = 0;
		break;

	case EXPP_SEQ_ATTR_STARTOFS:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"This property dosnt apply to an effect");
		CLAMP(number, 0, seq->len - seq->endofs);
		origval = seq->startofs;
		seq->startofs = number;
		regen_data = 1;
		break;
	case EXPP_SEQ_ATTR_ENDOFS:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"This property dosnt apply to an effect");
		CLAMP(number, 0, seq->len - seq->startofs);
		origval = seq->endofs;
		seq->endofs = number;
		regen_data = 1;
		break;
	case EXPP_SEQ_ATTR_STARTSTILL:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"This property dosnt apply to an effect");
		CLAMP(number, 1, MAXFRAME);
		origval = seq->startstill;
		seq->startstill = number;
		regen_data = 1;
		break;
	case EXPP_SEQ_ATTR_ENDSTILL:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"This property dosnt apply to an effect");
		CLAMP(number, seq->startstill + 1, MAXFRAME);
		origval = seq->endstill;
		seq->endstill = number;
		regen_data = 1;
		break;
	case EXPP_SEQ_ATTR_LENGTH:
		if (self->seq->type == SEQ_EFFECT)
			return EXPP_ReturnIntError(PyExc_RuntimeError,
									"cannot set the length of an effect directly");
		CLAMP(number, 1, MAXFRAME);
		origval = seq->len;
		seq->len = number;
		regen_data = 1;
		break;
	default:
		return EXPP_ReturnIntError(PyExc_RuntimeError,
								"undefined type in setFloatAttrClamp");
	}

	if (number != origval)
	{
		intern_pos_update(seq);

		if (GET_INT_FROM_POINTER(type) == EXPP_SEQ_ATTR_START)
			intern_recursive_pos_update(seq, origval - seq->start);

		if (regen_data)
		{
			new_tstripdata(seq);
		}

		calc_sequence(seq);
		calc_sequence_disp(seq);
	}
	return 0;
}

static PyObject *getFlagAttr(BPy_Sequence *self, void *type)
{
	if (self->seq->flag & GET_INT_FROM_POINTER(type))
		Py_RETURN_TRUE;
	else
		Py_RETURN_FALSE;
}

/*
 * set floating point attributes which require clamping
 */

static int setFlagAttr(BPy_Sequence *self, PyObject *value, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	int param = PyObject_IsTrue(value);

	if (param == -1)
		return EXPP_ReturnIntError(PyExc_TypeError,
								"expected True/False or 0/1");

	if (param)
		self->seq->flag |= t;
	else
	{
		/* dont allow leftsel and rightsel when its not selected */
		if (t == SELECT)
			t = t + SEQ_LEFTSEL + SEQ_RIGHTSEL;

		self->seq->flag &= ~t;
	}
	return 0;
}

static PyObject *getEffectSeq(BPy_Sequence *self, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	Sequence *seq = NULL;
	switch (t)
	{
	case 1:
		seq = self->seq->seq1;
		break;
	case 2:
		seq = self->seq->seq2;
		break;
	case 3:
		seq = self->seq->seq3;
		break;
	}

	if (seq)
	{
		return Sequence_CreatePyObject(seq, NULL, self->scene);
	}
	else
	{
		Py_RETURN_NONE;
	}
}

/*
 * set one of the effect sequences
 */

static int setEffectSeq(BPy_Sequence *self, PyObject *value, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	Sequence **seq;
	if ((value == Py_None || BPy_Sequence_Check(value)) == 0)
		return EXPP_ReturnIntError(PyExc_TypeError,
								"expected Sequence or None");

	switch (t)
	{
	case 1:
		seq = &self->seq->seq1;
		break;
	case 2:
		seq = &self->seq->seq2;
		break;
	case 3:
		seq = &self->seq->seq3;
		break;
	}

	if (value == Py_None)
		*seq = NULL;
	else
	{
		Sequence *newseq = ((BPy_Sequence *) value)->seq;
		if (newseq == self->seq)
		{
			return EXPP_ReturnIntError(PyExc_TypeError, "cannot set a sequence as its own effect");
		}

		*seq = ((BPy_Sequence *) value)->seq;
	}


	calc_sequence(self->seq);
	update_changed_seq_and_deps(self->seq, 1, 1);

	return 0;
}



static PyObject *getSpeedEffect(BPy_Sequence *self, PyObject *value, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	Sequence *seq= self->seq;
	SpeedControlVars * v;

	if (seq->type != SEQ_SPEED)
		return EXPP_ReturnPyObjError(PyExc_TypeError, "Not a speed effect strip" );

	v = (SpeedControlVars *)seq->effectdata;

	switch (t) {
	case EXPP_SEQ_ATTR_EFFECT_GLOBAL_SPEED:
		return PyFloat_FromDouble(v->globalSpeed);
		break;
	case EXPP_SEQ_ATTR_EFFECT_IPO_IS_VELOCITY:
		return PyBool_FromLong(v->flags & SEQ_SPEED_INTEGRATE);
		break;
	case EXPP_SEQ_ATTR_EFFECT_FRAME_BLENDING:
		return PyBool_FromLong(v->flags & SEQ_SPEED_BLEND);
		break;
	case EXPP_SEQ_ATTR_EFFECT_NORMALIZE_IPO_0_1:
		return PyBool_FromLong(v->flags & SEQ_SPEED_COMPRESS_IPO_Y);
		break;
	}

	if (PyErr_Occurred()) {
		return NULL;
	}

	Py_RETURN_NONE;
}

/*
 * set one of the effect sequences
 */

static int setSpeedEffect(BPy_Sequence *self, PyObject *value, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	Sequence *seq= self->seq;
	SpeedControlVars * v;

	if (seq->type != SEQ_SPEED)
		return EXPP_ReturnIntError(PyExc_TypeError, "Not a speed effect strip" );

	v = (SpeedControlVars *)seq->effectdata;

	switch (t) {
	case EXPP_SEQ_ATTR_EFFECT_GLOBAL_SPEED:
		v->globalSpeed= PyFloat_AsDouble(value);
		CLAMP(v->globalSpeed, 0.0f, 100.0f);
		break;
	case EXPP_SEQ_ATTR_EFFECT_IPO_IS_VELOCITY:
		if (PyObject_IsTrue( value ))	v->flags |=  SEQ_SPEED_INTEGRATE;
		else							v->flags &= ~SEQ_SPEED_INTEGRATE;
		break;
	case EXPP_SEQ_ATTR_EFFECT_FRAME_BLENDING:
		if (PyObject_IsTrue( value ))	v->flags |=  SEQ_SPEED_BLEND;
		else							v->flags &= ~SEQ_SPEED_BLEND;
		break;
	case EXPP_SEQ_ATTR_EFFECT_NORMALIZE_IPO_0_1:
		if (PyObject_IsTrue( value ))	v->flags |=  SEQ_SPEED_COMPRESS_IPO_Y;
		else							v->flags &= ~SEQ_SPEED_COMPRESS_IPO_Y;
		break;
	}

	if (PyErr_Occurred()) {
		return -1;
	}

	return 0;
}



static PyObject *getWipeEffect(BPy_Sequence *self, PyObject *value, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	Sequence *seq= self->seq;
	WipeVars * v;

	if (seq->type != SEQ_WIPE)
		return EXPP_ReturnPyObjError(PyExc_TypeError, "Not a wipe effect strip" );

	v = (WipeVars *)seq->effectdata;
	
	switch (t) {
	case EXPP_SEQ_ATTR_EFFECT_ANGLE:
		return PyFloat_FromDouble(v->angle);
		break;
	case EXPP_SEQ_ATTR_EFFECT_BLUR:
		return PyFloat_FromDouble(v->edgeWidth);
		break;
	case EXPP_SEQ_ATTR_EFFECT_WIPE_IN:
		return PyBool_FromLong(v->forward);
		break;
	}

	if (PyErr_Occurred()) {
		return NULL;
	}

	Py_RETURN_NONE;
}

/*
 * set one of the effect sequences
 */

static int setWipeEffect(BPy_Sequence *self, PyObject *value, void *type)
{
	int t = GET_INT_FROM_POINTER(type);
	Sequence *seq= self->seq;
	WipeVars * v;

	if (seq->type != SEQ_WIPE)
		return EXPP_ReturnIntError(PyExc_TypeError, "Not a wipe effect strip" );

	v = (WipeVars *)seq->effectdata;

	switch (t) {
	case EXPP_SEQ_ATTR_EFFECT_ANGLE:
		v->angle= PyFloat_AsDouble(value);
		CLAMP(v->angle, -90.0f, 90.0f);
		break;
	case EXPP_SEQ_ATTR_EFFECT_BLUR:
		v->edgeWidth= PyFloat_AsDouble(value);
		CLAMP(v->edgeWidth, -90.0f, 90.0f);
		break;
	case EXPP_SEQ_ATTR_EFFECT_WIPE_IN:
		if (PyObject_IsTrue( value ))	v->forward= 1;
		else							v->forward= 0;
		break;
	}

	if (PyErr_Occurred()) {
		return -1;
	}

	return 0;
}



/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef BPy_Sequence_getseters[] = {
	{"name",
		(getter) Sequence_getName, (setter) Sequence_setName,
		"Sequence name",
		NULL},
	{"proxyDir",
		(getter) Sequence_getProxyDir, (setter) Sequence_setProxyDir,
		"Sequence proxy directory",
		NULL},
	{"ipo",
		(getter) Sequence_getIpo, (setter) Sequence_setIpo,
		"Sequence ipo",
		NULL},

	{"scene",
		(getter) Sequence_getScene, (setter) NULL,
		"Sequence scene",
		NULL},
	{"sound",
		(getter) Sequence_getSound, (setter) NULL,
		"Sequence name",
		NULL},
	{"images",
		(getter) Sequence_getImages, (setter) Sequence_setImages,
		"Sequence scene",
		NULL},
	{"blendMode",
		(getter) Sequence_getBlendMode, (setter) Sequence_setBlendMode,
		"Sequence Blend Mode",
		NULL},

	{"type",
		(getter) getIntAttr, (setter) NULL,
		"",
		(void *) EXPP_SEQ_ATTR_TYPE},
	{"channel",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_CHAN},

	{"length",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_LENGTH},
	{"start",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_START},
	{"startOffset",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_STARTOFS},
	{"endOffset",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_ENDOFS},
	{"startStill",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_STARTSTILL},
	{"endStill",
		(getter) getIntAttr, (setter) setIntAttrClamp,
		"",
		(void *) EXPP_SEQ_ATTR_ENDSTILL},
	{"startDisp",
		(getter) getIntAttr, (setter) NULL,
		"",
		(void *) EXPP_SEQ_ATTR_STARTDISP},
	{"endDisp",
		(getter) getIntAttr, (setter) NULL,
		"",
		(void *) EXPP_SEQ_ATTR_ENDDISP},

	{"sel",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"Sequence audio mute option",
		(void *) SELECT},
	{"selLeft",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_LEFTSEL},
	{"selRight",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_RIGHTSEL},
	{"filtery",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_FILTERY},
	{"flipX",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_FLIPX},
	{"flipY",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_FLIPY},
	{"mute",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_MUTE},
	{"floatBuffer",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_MAKE_FLOAT},
	{"lock",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_LOCK},
	{"useProxy",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_USE_PROXY},
	{"premul",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_MAKE_PREMUL},
	{"reversed",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_REVERSE_FRAMES},
	{"ipoLocked",
		(getter) getFlagAttr, (setter) setFlagAttr,
		"",
		(void *) SEQ_IPO_FRAME_LOCKED},
	{"seq1",
		(getter) getEffectSeq, (setter) setEffectSeq,
		"",
		(void *) 1},
	{"seq2",
		(getter) getEffectSeq, (setter) setEffectSeq,
		"",
		(void *) 2},
	{"seq3",
		(getter) getEffectSeq, (setter) setEffectSeq,
		"",
		(void *) 3},

	/* effects */
	{"speedEffectGlobalSpeed",
		(getter) getSpeedEffect, (setter) setSpeedEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_GLOBAL_SPEED},
	{"speedEffectIpoVelocity",
		(getter) getSpeedEffect, (setter) setSpeedEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_IPO_IS_VELOCITY},
	{"speedEffectFrameBlending",
		(getter) getSpeedEffect, (setter) setSpeedEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_FRAME_BLENDING},
	{"speedEffectIpoNormalize",
		(getter) getSpeedEffect, (setter) setSpeedEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_NORMALIZE_IPO_0_1},

	{"wipeEffectAngle",
		(getter) getWipeEffect, (setter) setWipeEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_ANGLE},
	{"wipeEffectBlur",
		(getter) getWipeEffect, (setter) setWipeEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_BLUR},
	{"wipeEffectWipeIn",
		(getter) getWipeEffect, (setter) setWipeEffect,
		"",
		(void *) EXPP_SEQ_ATTR_EFFECT_WIPE_IN},
	
	{NULL, NULL, NULL, NULL, NULL} /* Sentinel */
};

/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef BPy_SceneSeq_getseters[] = {
	{"active",
		(getter) SceneSeq_getActive, (setter) NULL,
		"the active strip",
		NULL},
	{"metastrip",
		(getter) SceneSeq_getMetaStrip, (setter) NULL,
		"The currently active metastrip the user is editing",
		NULL},
	{NULL, NULL, NULL, NULL, NULL} /* Sentinel */
};

/*****************************************************************************/
/* Python TypeSequence structure definition:                                 */
/*****************************************************************************/
PyTypeObject Sequence_Type = {
	PyObject_HEAD_INIT(NULL) /* required py macro */
	0, /* ob_size */
	/*  For printing, in format "<module>.<name>" */
	"Blender Sequence", /* char *tp_name; */
	sizeof ( BPy_Sequence), /* int tp_basicsize; */
	0, /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	NULL, /* destructor tp_dealloc; */
	NULL, /* printfunc tp_print; */
	NULL, /* getattrfunc tp_getattr; */
	NULL, /* setattrfunc tp_setattr; */
	(cmpfunc) Sequence_compare, /* cmpfunc tp_compare; */
	(reprfunc) Sequence_repr, /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL, /* PyNumberMethods *tp_as_number; */
	NULL, /* PySequenceMethods *tp_as_sequence; */
	NULL, /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL, /* hashfunc tp_hash; */
	NULL, /* ternaryfunc tp_call; */
	NULL, /* reprfunc tp_str; */
	NULL, /* getattrofunc tp_getattro; */
	NULL, /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL, /* PyBufferProcs *tp_as_buffer; */

	/*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT, /* long tp_flags; */

	NULL, /*  char *tp_doc;  Documentation string */
	/*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL, /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL, /* inquiry tp_clear; */

	/***  Assigned meaning in release 2.1 ***/
	/*** rich comparisons ***/
	NULL, /* richcmpfunc tp_richcompare; */

	/***  weak reference enabler ***/
	0, /* long tp_weaklistoffset; */

	/*** Added in release 2.2 ***/
	/*   Iterators */
	(getiterfunc) Sequence_getIter, /* getiterfunc tp_iter; */
	(iternextfunc) Sequence_nextIter, /* iternextfunc tp_iternext; */

	/*** Attribute descriptor and subclassing stuff ***/
	BPy_Sequence_methods, /* struct PyMethodDef *tp_methods; */
	NULL, /* struct PyMemberDef *tp_members; */
	BPy_Sequence_getseters, /* struct PyGetSetDef *tp_getset; */
	NULL, /* struct _typeobject *tp_base; */
	NULL, /* PyObject *tp_dict; */
	NULL, /* descrgetfunc tp_descr_get; */
	NULL, /* descrsetfunc tp_descr_set; */
	0, /* long tp_dictoffset; */
	NULL, /* initproc tp_init; */
	NULL, /* allocfunc tp_alloc; */
	NULL, /* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL, /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL, /* inquiry tp_is_gc;  */
	NULL, /* PyObject *tp_bases; */
	/* method resolution order */
	NULL, /* PyObject *tp_mro;  */
	NULL, /* PyObject *tp_cache; */
	NULL, /* PyObject *tp_subclasses; */
	NULL, /* PyObject *tp_weaklist; */
	NULL
};



/*****************************************************************************/
/* Python TypeSequence structure definition:                                 */
/*****************************************************************************/
PyTypeObject SceneSeq_Type = {
	PyObject_HEAD_INIT(NULL) /* required py macro */
	0, /* ob_size */
	/*  For printing, in format "<module>.<name>" */
	"Blender SceneSeq", /* char *tp_name; */
	sizeof ( BPy_Sequence), /* int tp_basicsize; */
	0, /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	NULL, /* destructor tp_dealloc; */
	NULL, /* printfunc tp_print; */
	NULL, /* getattrfunc tp_getattr; */
	NULL, /* setattrfunc tp_setattr; */
	(cmpfunc) SceneSeq_compare, /* cmpfunc tp_compare; */
	(reprfunc) SceneSeq_repr, /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL, /* PyNumberMethods *tp_as_number; */
	NULL, /* PySequenceMethods *tp_as_sequence; */
	NULL, /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL, /* hashfunc tp_hash; */
	NULL, /* ternaryfunc tp_call; */
	NULL, /* reprfunc tp_str; */
	NULL, /* getattrofunc tp_getattro; */
	NULL, /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL, /* PyBufferProcs *tp_as_buffer; */

	/*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT, /* long tp_flags; */

	NULL, /*  char *tp_doc;  Documentation string */
	/*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL, /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL, /* inquiry tp_clear; */

	/***  Assigned meaning in release 2.1 ***/
	/*** rich comparisons ***/
	NULL, /* richcmpfunc tp_richcompare; */

	/***  weak reference enabler ***/
	0, /* long tp_weaklistoffset; */

	/*** Added in release 2.2 ***/
	/*   Iterators */
	(getiterfunc) SceneSeq_getIter, /* getiterfunc tp_iter; */
	(iternextfunc) SceneSeq_nextIter, /* iternextfunc tp_iternext; */

	/*** Attribute descriptor and subclassing stuff ***/
	BPy_SceneSeq_methods, /* struct PyMethodDef *tp_methods; */
	NULL, /* struct PyMemberDef *tp_members; */
	BPy_SceneSeq_getseters, /* struct PyGetSetDef *tp_getset; */
	NULL, /* struct _typeobject *tp_base; */
	NULL, /* PyObject *tp_dict; */
	NULL, /* descrgetfunc tp_descr_get; */
	NULL, /* descrsetfunc tp_descr_set; */
	0, /* long tp_dictoffset; */
	NULL, /* initproc tp_init; */
	NULL, /* allocfunc tp_alloc; */
	NULL, /* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL, /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL, /* inquiry tp_is_gc;  */
	NULL, /* PyObject *tp_bases; */
	/* method resolution order */
	NULL, /* PyObject *tp_mro;  */
	NULL, /* PyObject *tp_cache; */
	NULL, /* PyObject *tp_subclasses; */
	NULL, /* PyObject *tp_weaklist; */
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
PyObject *Sequence_Init(void)
{
	PyObject *BlendModesDict = M_Sequence_BlendModesDict();
	PyObject *submodule;
	if (PyType_Ready(&Sequence_Type) < 0)
		return NULL;
	if (PyType_Ready(&SceneSeq_Type) < 0)
		return NULL;

	/* NULL was M_Sequence_methods*/
	submodule = Py_InitModule3("Blender.Scene.Sequence", NULL,
							"The Blender Sequence module\n\n\
This module provides access to **Sequence Data** in Blender.\n");

	if (BlendModesDict)
		PyModule_AddObject(submodule, "BlendModes", BlendModesDict);

	/*Add SUBMODULES to the module*/
	/*PyDict_SetItemString(dict, "Constraint", Constraint_Init()); //creates a *new* module*/
	return submodule;
}


/*****************************************************************************/
/* Function:	Sequence_CreatePyObject					 */
/* Description: This function will create a new BlenObject from an existing  */
/*		Object structure.					 */

/*****************************************************************************/
PyObject *Sequence_CreatePyObject(struct Sequence * seq, struct Sequence * iter, struct Scene *sce)
{
	BPy_Sequence *pyseq;

	if (!seq)
		Py_RETURN_NONE;

	pyseq =
		(BPy_Sequence *) PyObject_NEW(BPy_Sequence, &Sequence_Type);

	if (pyseq == NULL)
	{
		return ( NULL);
	}
	pyseq->seq = seq;
	pyseq->iter = iter;
	pyseq->scene = sce;

	return ( (PyObject *) pyseq);
}

/*****************************************************************************/
/* Function:	SceneSeq_CreatePyObject					 */
/* Description: This function will create a new BlenObject from an existing  */
/*		Object structure.					 */

/*****************************************************************************/
PyObject *SceneSeq_CreatePyObject(struct Scene * scn, struct Sequence * iter)
{
	BPy_SceneSeq *pysceseq;

	if (!scn)
		Py_RETURN_NONE;

	if (!scn->ed)
	{
		Editing *ed;
		ed = scn->ed = MEM_callocN(sizeof (Editing), "addseq");
		ed->seqbasep = &ed->seqbase;
	}

	pysceseq =
		(BPy_SceneSeq *) PyObject_NEW(BPy_SceneSeq, &SceneSeq_Type);

	if (pysceseq == NULL)
	{
		return ( NULL);
	}
	pysceseq->scene = scn;
	pysceseq->iter = iter;

	return ( (PyObject *) pysceseq);
}

/*****************************************************************************/
/* Function:	Sequence_FromPyObject					 */
/* Description: This function returns the Blender sequence from the given	 */
/*		PyObject.						 */

/*****************************************************************************/
struct Sequence *Sequence_FromPyObject(PyObject * py_seq)
{
	BPy_Sequence *blen_seq;

	blen_seq = (BPy_Sequence *) py_seq;
	return ( blen_seq->seq);
}

/*****************************************************************************/
/* Function:	Sequence_compare						 */
/* Description: This is a callback function for the BPy_Sequence type. It	 */
/*		compares two Sequence_Type objects. Only the "==" and "!="  */
/*		comparisons are meaninful. Returns 0 for equality and -1 if  */
/*		they don't point to the same Blender Object struct.	 */
/*		In Python it becomes 1 if they are equal, 0 otherwise.	 */

/*****************************************************************************/
static int Sequence_compare(BPy_Sequence * a, BPy_Sequence * b)
{
	Sequence *pa = a->seq, *pb = b->seq;
	return ( pa == pb) ? 0 : -1;
}

static int SceneSeq_compare(BPy_SceneSeq * a, BPy_SceneSeq * b)
{

	Scene *pa = a->scene, *pb = b->scene;
	return ( pa == pb) ? 0 : -1;
}

/*****************************************************************************/
/* Function:	Sequence_repr / SceneSeq_repr						 */
/* Description: This is a callback function for the BPy_Sequence type. It	 */
/*		builds a meaninful string to represent object objects.	 */

/*****************************************************************************/
static PyObject *Sequence_repr(BPy_Sequence * self)
{
	return PyString_FromFormat("[Sequence Strip \"%s\"]",
							self->seq->name + 2);
}

static PyObject *SceneSeq_repr(BPy_SceneSeq * self)
{
	return PyString_FromFormat("[Scene Sequence \"%s\"]",
							self->scene->id.name + 2);
}

