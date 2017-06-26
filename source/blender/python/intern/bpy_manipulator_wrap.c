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
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/python/intern/bpy_manipulator_wrap.c
 *  \ingroup pythonintern
 *
 * This file is so Python can define widget-group's that C can call into.
 * The generic callback functions for Python widget-group are defines in
 * 'rna_wm.c', some calling into functions here to do python specific
 * functionality.
 *
 * \note This follows 'bpy_operator_wrap.c' very closely.
 * Keep in sync unless there is good reason not to!
 */

#include <Python.h>

#include "BLI_utildefines.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "bpy_rna.h"
#include "bpy_intern_string.h"
#include "bpy_manipulator_wrap.h"  /* own include */

/* we may want to add, but not now */

/* -------------------------------------------------------------------- */

/** \name Manipulator
 * \{ */


static bool bpy_manipulatortype_target_property_def(
        wmManipulatorType *wt, PyObject *item)
{
	/* Note: names based on 'rna_rna.c' */
	PyObject *empty_tuple = PyTuple_New(0);

	struct {
		char *id;
		char *type_id; int type;
		int array_length;
	} params = {
		.id = NULL, /* not optional */
		.type = PROP_FLOAT,
		.type_id = NULL,
		.array_length = 1,
	};

	static const char * const _keywords[] = {"id", "type", "array_length", NULL};
#define KW_FMT "|$ssi:register_class"
#if PY_VERSION_HEX >= 0x03060000
	static _PyArg_Parser _parser = {KW_FMT, _keywords, 0};
	if (!_PyArg_ParseTupleAndKeywordsFast(
	        empty_tuple, item,
	        &_parser,
	        &params.id,
	        &params.type_id,
	        &params.array_length))
#else
	if (!PyArg_ParseTupleAndKeywords(
	        empty_tuple, item,
	        KW_FMT, (char **)_keywords,
	        &params.id,
	        &params.type_id,
	        &params.array_length))
#endif
	{
		goto fail;
	}
#undef KW_FMT

	if (params.id == NULL) {
		PyErr_SetString(PyExc_ValueError, "'id' argument not given");
		goto fail;
	}

	if ((params.type_id != NULL) &&
	    pyrna_enum_value_from_id(
	        rna_enum_property_type_items, params.type_id, &params.type, "'type' enum value") == -1)
	{
		goto fail;
	}
	else {
		params.type = rna_enum_property_type_items[params.type].value;
	}

	if ((params.array_length < 1 || params.array_length > RNA_MAX_ARRAY_LENGTH)) {
		PyErr_SetString(PyExc_ValueError, "'array_length' out of range");
		goto fail;
	}

	WM_manipulatortype_target_property_def(wt, params.id, params.type, params.array_length);
	Py_DECREF(empty_tuple);
	return true;

fail:
	Py_DECREF(empty_tuple);
	return false;
}

static void manipulator_properties_init(wmManipulatorType *wt)
{
	PyTypeObject *py_class = wt->ext.data;
	RNA_struct_blender_type_set(wt->ext.srna, wt);

	/* only call this so pyrna_deferred_register_class gives a useful error
	 * WM_operatortype_append_ptr will call RNA_def_struct_identifier
	 * later */
	RNA_def_struct_identifier(wt->srna, wt->idname);

	if (pyrna_deferred_register_class(wt->srna, py_class) != 0) {
		PyErr_Print(); /* failed to register operator props */
		PyErr_Clear();
	}

	/* Extract target property definitions from 'bl_target_properties' */
	{
		/* picky developers will notice that 'bl_targets' won't work with inheritance
		 * get direct from the dict to avoid raising a load of attribute errors (yes this isnt ideal) - campbell */
		PyObject *py_class_dict = py_class->tp_dict;
		PyObject *bl_target_properties = PyDict_GetItem(py_class_dict, bpy_intern_str_bl_target_properties);
		PyObject *bl_target_properties_fast;

		if (!(bl_target_properties_fast = PySequence_Fast(bl_target_properties, "bl_target_properties sequence"))) {
			/* PySequence_Fast sets the error */
			PyErr_Print();
			PyErr_Clear();
			return;
		}

		const uint items_len = PySequence_Fast_GET_SIZE(bl_target_properties_fast);
		PyObject **items = PySequence_Fast_ITEMS(bl_target_properties_fast);

		for (uint i = 0; i < items_len; i++) {
			if (!bpy_manipulatortype_target_property_def(wt, items[i])) {
				PyErr_Print();
				PyErr_Clear();
				break;
			}
		}

		Py_DECREF(bl_target_properties_fast);
	}
}

void BPY_RNA_manipulator_wrapper(wmManipulatorType *wt, void *userdata)
{
	/* take care not to overwrite anything set in
	 * WM_manipulatormaptype_group_link_ptr before opfunc() is called */
	StructRNA *srna = wt->srna;
	*wt = *((wmManipulatorType *)userdata);
	wt->srna = srna; /* restore */

	/* don't do translations here yet */
#if 0
	/* Use i18n context from ext.srna if possible (py manipulatorgroups). */
	if (wt->ext.srna) {
		RNA_def_struct_translation_context(wt->srna, RNA_struct_translation_context(wt->ext.srna));
	}
#endif

	wt->struct_size = sizeof(wmManipulator);

	manipulator_properties_init(wt);
}

/** \} */


/* -------------------------------------------------------------------- */

/** \name Manipulator Group
 * \{ */

static void manipulatorgroup_properties_init(wmManipulatorGroupType *wgt)
{
#ifdef USE_SRNA
	PyTypeObject *py_class = wgt->ext.data;
#endif
	RNA_struct_blender_type_set(wgt->ext.srna, wgt);

#ifdef USE_SRNA
	/* only call this so pyrna_deferred_register_class gives a useful error
	 * WM_operatortype_append_ptr will call RNA_def_struct_identifier
	 * later */
	RNA_def_struct_identifier(wgt->srna, wgt->idname);

	if (pyrna_deferred_register_class(wgt->srna, py_class) != 0) {
		PyErr_Print(); /* failed to register operator props */
		PyErr_Clear();
	}
#endif
}

void BPY_RNA_manipulatorgroup_wrapper(wmManipulatorGroupType *wgt, void *userdata)
{
	/* take care not to overwrite anything set in
	 * WM_manipulatormaptype_group_link_ptr before opfunc() is called */
#ifdef USE_SRNA
	StructRNA *srna = wgt->srna;
#endif
	*wgt = *((wmManipulatorGroupType *)userdata);
#ifdef USE_SRNA
	wgt->srna = srna; /* restore */
#endif

#ifdef USE_SRNA
	/* Use i18n context from ext.srna if possible (py manipulatorgroups). */
	if (wgt->ext.srna) {
		RNA_def_struct_translation_context(wgt->srna, RNA_struct_translation_context(wgt->ext.srna));
	}
#endif

	manipulatorgroup_properties_init(wgt);
}

/** \} */

