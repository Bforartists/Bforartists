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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Blender Foundation (2009), Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"

#include "rna_internal.h"

#include "DNA_gpencil_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

static int rna_GPencilLayer_active_frame_editable(PointerRNA *ptr)
{
	bGPDlayer *gpl= (bGPDlayer *)ptr->data;
	
	/* surely there must be other criteria too... */
	if (gpl->flag & GP_LAYER_LOCKED)
		return 0;
	else
		return 1;
}

static void rna_GPencilLayer_active_set(PointerRNA *ptr, int value)
{
	bGPdata *gpd= ptr->id.data;
	bGPDlayer *gpl= ptr->data;
	
	/* disabled all other layers anyway */
	if (GS(gpd->id.name) == ID_GD) {
		bGPDlayer *gl;
		
		for (gl= gpd->layers.first; gl; gl= gl->next)
			gl->flag &= ~GP_LAYER_ACTIVE;
	}	
	
	/* if enabling value, make it active */
	if (value)
		gpl->flag |= GP_LAYER_ACTIVE;
}

#else

static void rna_def_gpencil_stroke_point(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "GPencilStrokePoint", NULL);
	RNA_def_struct_sdna(srna, "bGPDspoint");
	RNA_def_struct_ui_text(srna, "Grease Pencil Stroke Point", "Data point for freehand stroke curve");
	
	prop= RNA_def_property(srna, "co", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_float_sdna(prop, NULL, "x");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Coordinates", "");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "pressure", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "pressure");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Pressure", "Pressure of tablet at point when drawing it");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
}

static void rna_def_gpencil_stroke(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "GPencilStroke", NULL);
	RNA_def_struct_sdna(srna, "bGPDstroke");
	RNA_def_struct_ui_text(srna, "Grease Pencil Stroke", "Freehand curve defining part of a sketch");
	
	/* Points */
	prop= RNA_def_property(srna, "points", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "points", "totpoints");
	RNA_def_property_struct_type(prop, "GPencilStrokePoint");
	RNA_def_property_ui_text(prop, "Stroke Points", "Stroke data points");
	
	/* Flags - Readonly type-info really... */
	// TODO...
}

static void rna_def_gpencil_frame(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "GPencilFrame", NULL);
	RNA_def_struct_sdna(srna, "bGPDframe");
	RNA_def_struct_ui_text(srna, "Grease Pencil Frame", "Collection of related sketches on a particular frame");
	
	/* Strokes */
	prop= RNA_def_property(srna, "strokes", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "strokes", NULL);
	RNA_def_property_struct_type(prop, "GPencilStroke");
	RNA_def_property_ui_text(prop, "Strokes", "Freehand curves defining the sketch on this frame");
	
	/* Frame Number */
	prop= RNA_def_property(srna, "frame_number", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "framenum");
	RNA_def_property_range(prop, MINFRAME, MAXFRAME); // XXX note: this cannot occur on the same frame as another sketch
	RNA_def_property_ui_text(prop, "Frame Number", "The frame on which this sketch appears");
	
	/* Flags */
	prop= RNA_def_property(srna, "is_edited", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_FRAME_PAINT); // XXX should it be editable?
	RNA_def_property_ui_text(prop, "Paint Lock", "Frame is being edited (painted on)");
	
	prop= RNA_def_property(srna, "select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_FRAME_SELECT);
	RNA_def_property_ui_text(prop, "Select", "Frame is selected for editing in the DopeSheet");
}

static void rna_def_gpencil_layer(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "GPencilLayer", NULL);
	RNA_def_struct_sdna(srna, "bGPDlayer");
	RNA_def_struct_ui_text(srna, "Grease Pencil Layer", "Collection of related sketches");
	
	/* Name */
	prop= RNA_def_property(srna, "info", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Info", "Layer name");
	RNA_def_struct_name_property(srna, prop);
	
	/* Frames */
	prop= RNA_def_property(srna, "frames", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "frames", NULL);
	RNA_def_property_struct_type(prop, "GPencilFrame");
	RNA_def_property_ui_text(prop, "Frames", "Sketches for this layer on different frames");
	
	/* Active Frame */
	prop= RNA_def_property(srna, "active_frame", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "actframe");
	RNA_def_property_ui_text(prop, "Active Frame", "Frame currently being displayed for this layer");
	RNA_def_property_editable_func(prop, "rna_GPencilLayer_active_frame_editable");
	
	/* Drawing Color */
	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Color", "Color for all strokes in this layer");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "alpha", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "color[3]");
	RNA_def_property_range(prop, 0.3, 1.0f);
	RNA_def_property_ui_text(prop, "Opacity", "Layer Opacity");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	/* Line Thickness */
	prop= RNA_def_property(srna, "line_width", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "thickness");
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_text(prop, "Thickness", "Thickness of strokes (in pixels)");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	/* Onion-Skinning */
	prop= RNA_def_property(srna, "use_onion_skinning", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_ONIONSKIN);
	RNA_def_property_ui_text(prop, "Use Onion Skinning", "Ghost frames on either side of frame");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "ghost_range_max", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gstep");
	RNA_def_property_range(prop, 0, 120);
	RNA_def_property_ui_text(prop, "Max Ghost Range", "Maximum number of frames on either side of the active frame to show (0 = show the 'first' available sketch on either side)");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	/* Flags */
	prop= RNA_def_property(srna, "hide", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_HIDE);
	RNA_def_property_ui_text(prop, "Hide", "Set layer Visibility");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "lock", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_LOCKED);
	RNA_def_property_ui_text(prop, "Locked", "Protect layer from further editing and/or frame changes");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "lock_frame", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_FRAMELOCK);
	RNA_def_property_ui_text(prop, "Frame Locked", "Lock current frame displayed by layer");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_ACTIVE);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_GPencilLayer_active_set");
	RNA_def_property_ui_text(prop, "Active", "Set active layer for editing");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
	prop= RNA_def_property(srna, "select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_SELECT);
	RNA_def_property_ui_text(prop, "Select", "Layer is selected for editing in the DopeSheet");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
	
		// XXX keep this option?
	prop= RNA_def_property(srna, "show_points", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_LAYER_DRAWDEBUG);
	RNA_def_property_ui_text(prop, "Show Points", "Draw the points which make up the strokes (for debugging purposes)");
	RNA_def_property_update(prop, NC_SCREEN|ND_GPENCIL, NULL);
}

static void rna_def_gpencil_data(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem draw_mode_items[] = {
		{GP_DATA_VIEWALIGN, "CURSOR", 0, "Cursor", "Draw stroke at the 3D cursor"},
		{0, "VIEW", 0, "View", "Stick stroke to the view "}, /* weired, GP_DATA_VIEWALIGN is inverted */
		{GP_DATA_VIEWALIGN|GP_DATA_DEPTH_VIEW, "SURFACE", 0, "Surface", "Stick stroke to surfaces"},
		{GP_DATA_VIEWALIGN|GP_DATA_DEPTH_STROKE, "STROKE", 0, "Stroke", "Stick stroke to other strokes"},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "GreasePencil", "ID");
	RNA_def_struct_sdna(srna, "bGPdata");
	RNA_def_struct_ui_text(srna, "Grease Pencil", "Freehand annotation sketchbook");
	RNA_def_struct_ui_icon(srna, ICON_GREASEPENCIL);
	
	/* Layers */
	prop= RNA_def_property(srna, "layers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "layers", NULL);
	RNA_def_property_struct_type(prop, "GPencilLayer");
	RNA_def_property_ui_text(prop, "Layers", "");
	
	/* Flags */
	prop= RNA_def_property(srna, "draw_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "flag");
	RNA_def_property_enum_items(prop, draw_mode_items);
	RNA_def_property_ui_text(prop, "Draw Mode", "");

	prop= RNA_def_property(srna, "use_stroke_endpoints", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_DATA_DEPTH_STROKE_ENDPOINTS);
	RNA_def_property_ui_text(prop, "Only Endpoints", "Only use the first and last parts of the stroke for snapping");


}

/* --- */

void RNA_def_gpencil(BlenderRNA *brna)
{
	rna_def_gpencil_data(brna);
	
	rna_def_gpencil_layer(brna);
	rna_def_gpencil_frame(brna);
	rna_def_gpencil_stroke(brna);
	rna_def_gpencil_stroke_point(brna);
}

#endif
