/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "DNA_color_types.h"

#ifdef RNA_RUNTIME

#include "BKE_colortools.h"

static int rna_CurveMapping_curves_length(PointerRNA *ptr)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;
	int len;

	for(len=0; len<CM_TOT; len++)
		if(!cumap->cm[len].curve)
			break;
	
	return len;
}

static void rna_CurveMapping_curves_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;

	rna_iterator_array_begin(iter, cumap->cm, sizeof(CurveMap), rna_CurveMapping_curves_length(ptr), NULL);
}

static void rna_CurveMapping_use_clipping_set(PointerRNA *ptr, int value)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;

	if(value) cumap->flag |= CUMA_DO_CLIP;
	else cumap->flag &= ~CUMA_DO_CLIP;

	curvemapping_changed(cumap, 0);
}

static void rna_CurveMapping_black_level_set(PointerRNA *ptr, int index, float value)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;
	cumap->black[index]= value;
	curvemapping_set_black_white(cumap, NULL, NULL);
}

static void rna_CurveMapping_white_level_set(PointerRNA *ptr, int index, float value)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;
	cumap->white[index]= value;
	curvemapping_set_black_white(cumap, NULL, NULL);
}

static void rna_CurveMapping_clipminx_range(PointerRNA *ptr, float *min, float *max)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;

	*min= -100.0f;
	*max= cumap->clipr.xmax;
}

static void rna_CurveMapping_clipminy_range(PointerRNA *ptr, float *min, float *max)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;

	*min= -100.0f;
	*max= cumap->clipr.ymax;
}

static void rna_CurveMapping_clipmaxx_range(PointerRNA *ptr, float *min, float *max)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;

	*min= cumap->clipr.xmin;
	*max= 100.0f;
}

static void rna_CurveMapping_clipmaxy_range(PointerRNA *ptr, float *min, float *max)
{
	CurveMapping *cumap= (CurveMapping*)ptr->data;

	*min= cumap->clipr.ymin;
	*max= 100.0f;
}

#else

static void rna_def_curvemappoint(BlenderRNA *brna)
{
	StructRNA *srna;
    PropertyRNA *prop;
	static EnumPropertyItem prop_handle_type_items[] = {
        {0, "AUTO", "Auto Handle", ""},
        {CUMA_VECTOR, "VECTOR", "Vector Handle", ""},
		{0, NULL, NULL, NULL}
    };

	srna= RNA_def_struct(brna, "CurveMapPoint", NULL, "CurveMapPoint");

	/* not editable for now, need to have CurveMapping to do curvemapping_changed */

    prop= RNA_def_property(srna, "location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "x");
	RNA_def_property_array(prop, 2);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
    RNA_def_property_ui_text(prop, "Location", "");

	prop= RNA_def_property(srna, "handle_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "flag", PROP_DEF_ENUM_BITFLAGS);
	RNA_def_property_enum_items(prop, prop_handle_type_items);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
    RNA_def_property_ui_text(prop, "Handle Type", "");

    prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CUMA_SELECT);
    RNA_def_property_ui_text(prop, "Selected", "");
}

static void rna_def_curvemap(BlenderRNA *brna)
{
	StructRNA *srna;
    PropertyRNA *prop;
	static EnumPropertyItem prop_extend_items[] = {
        {0, "HORIZONTAL", "Horizontal", ""},
        {CUMA_EXTEND_EXTRAPOLATE, "EXTRAPOLATED", "Extrapolated", ""},
		{0, NULL, NULL, NULL}
    };

	srna= RNA_def_struct(brna, "CurveMap", NULL, "CurveMap");

	/* not editable for now, need to have CurveMapping to do curvemapping_changed */

	prop= RNA_def_property(srna, "extend", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "flag", CUMA_EXTEND_EXTRAPOLATE);
	RNA_def_property_enum_items(prop, prop_extend_items);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
    RNA_def_property_ui_text(prop, "Extend", "");

    prop= RNA_def_property(srna, "points", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "curve", "totpoint");
    RNA_def_property_struct_type(prop, "CurveMapPoint");
    RNA_def_property_ui_text(prop, "Points", "");
}

static void rna_def_curvemapping(BlenderRNA *brna)
{
	StructRNA *srna;
    PropertyRNA *prop;

	srna= RNA_def_struct(brna, "CurveMapping", NULL, "CurveMapping");

    prop= RNA_def_property(srna, "use_clipping", PROP_BOOLEAN, PROP_NONE);
    RNA_def_property_boolean_sdna(prop, NULL, "flag", CUMA_DO_CLIP);
    RNA_def_property_ui_text(prop, "Use Clipping", "");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_CurveMapping_use_clipping_set");

    prop= RNA_def_property(srna, "clip_min_x", PROP_FLOAT, PROP_NONE);
    RNA_def_property_float_sdna(prop, NULL, "clipr.xmin");
	RNA_def_property_range(prop, -100.0f, 100.0f);
    RNA_def_property_ui_text(prop, "Clip Min X", "");
	RNA_def_property_float_funcs(prop, NULL, NULL, "rna_CurveMapping_clipminx_range");

    prop= RNA_def_property(srna, "clip_min_y", PROP_FLOAT, PROP_NONE);
    RNA_def_property_float_sdna(prop, NULL, "clipr.ymin");
	RNA_def_property_range(prop, -100.0f, 100.0f);
    RNA_def_property_ui_text(prop, "Clip Min Y", "");
	RNA_def_property_float_funcs(prop, NULL, NULL, "rna_CurveMapping_clipminy_range");

    prop= RNA_def_property(srna, "clip_max_x", PROP_FLOAT, PROP_NONE);
    RNA_def_property_float_sdna(prop, NULL, "clipr.xmax");
	RNA_def_property_range(prop, -100.0f, 100.0f);
    RNA_def_property_ui_text(prop, "Clip Max X", "");
	RNA_def_property_float_funcs(prop, NULL, NULL, "rna_CurveMapping_clipmaxx_range");

    prop= RNA_def_property(srna, "clip_max_y", PROP_FLOAT, PROP_NONE);
    RNA_def_property_float_sdna(prop, NULL, "clipr.ymax");
	RNA_def_property_range(prop, -100.0f, 100.0f);
    RNA_def_property_ui_text(prop, "Clip Max Y", "");
	RNA_def_property_float_funcs(prop, NULL, NULL, "rna_CurveMapping_clipmaxy_range");

	prop= RNA_def_property(srna, "curves", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_funcs(prop, "rna_CurveMapping_curves_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", 0, "rna_CurveMapping_curves_length", 0, 0);
	RNA_def_property_struct_type(prop, "CurveMap");
	RNA_def_property_ui_text(prop, "Curves", "");

    prop= RNA_def_property(srna, "black_level", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "black");
	RNA_def_property_ui_range(prop, 0.0f, 1.0f, 10, 3);
	RNA_def_property_ui_text(prop, "Black Level", "");
	RNA_def_property_float_funcs(prop, NULL, "rna_CurveMapping_black_level_set", NULL);

    prop= RNA_def_property(srna, "white_level", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "white");
	RNA_def_property_ui_range(prop, 0.0f, 1.0f, 10, 3);
	RNA_def_property_ui_text(prop, "White Level", "");
	RNA_def_property_float_funcs(prop, NULL, "rna_CurveMapping_white_level_set", NULL);
}

void RNA_def_color(BlenderRNA *brna)
{
	rna_def_curvemappoint(brna);
	rna_def_curvemap(brna);
	rna_def_curvemapping(brna);
}

#endif

