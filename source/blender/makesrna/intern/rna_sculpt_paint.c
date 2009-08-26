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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_scene_types.h"

#include "BKE_paint.h"

#ifdef RNA_RUNTIME

static PointerRNA rna_ParticleEdit_brush_get(PointerRNA *ptr)
{
	ParticleEditSettings *pset= (ParticleEditSettings*)ptr->data;
	ParticleBrushData *brush= NULL;;

	if(pset->brushtype != PE_BRUSH_NONE)
		brush= &pset->brush[pset->brushtype];

	return rna_pointer_inherit_refine(ptr, &RNA_ParticleBrush, brush);
}

static PointerRNA rna_ParticleBrush_curve_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_CurveMapping, NULL);
}

static void rna_Paint_brushes_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Paint *p= (Paint*)ptr->data;
	rna_iterator_array_begin(iter, (void*)p->brushes, sizeof(Brush*), p->brush_count, 0, NULL);
}

static int rna_Paint_brushes_length(PointerRNA *ptr)
{
	Paint *p= (Paint*)ptr->data;

	return p->brush_count;
}

static PointerRNA rna_Paint_active_brush_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_Brush, paint_brush(ptr->data));
}

static void rna_Paint_active_brush_set(PointerRNA *ptr, PointerRNA value)
{
	paint_brush_set(ptr->data, value.data);
}

#else

static void rna_def_paint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Paint", NULL);
	RNA_def_struct_ui_text(srna, "Paint", "");

	prop= RNA_def_property(srna, "brushes", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Brush");
	RNA_def_property_collection_funcs(prop, "rna_Paint_brushes_begin",
					  "rna_iterator_array_next",
					  "rna_iterator_array_end",
					  "rna_iterator_array_dereference_get", 
					  "rna_Paint_brushes_length", 0, 0, 0, 0);
	RNA_def_property_ui_text(prop, "Brushes", "Brushes selected for this paint mode.");

	prop= RNA_def_property(srna, "active_brush_index", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 0, INT_MAX);       

	/* Fake property to get active brush directly, rather than integer index */
	prop= RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Brush");
	RNA_def_property_pointer_funcs(prop, "rna_Paint_active_brush_get", "rna_Paint_active_brush_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Brush", "Active paint brush.");
}

static void rna_def_sculpt(BlenderRNA  *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Sculpt", "Paint");
	RNA_def_struct_ui_text(srna, "Sculpt", "");
	
	prop= RNA_def_property(srna, "symmetry_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_X);
	RNA_def_property_ui_text(prop, "Symmetry X", "Mirror brush across the X axis.");

	prop= RNA_def_property(srna, "symmetry_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_Y);
	RNA_def_property_ui_text(prop, "Symmetry Y", "Mirror brush across the Y axis.");

	prop= RNA_def_property(srna, "symmetry_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_Z);
	RNA_def_property_ui_text(prop, "Symmetry Z", "Mirror brush across the Z axis.");

	prop= RNA_def_property(srna, "lock_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_X);
	RNA_def_property_ui_text(prop, "Lock X", "Disallow changes to the X axis of vertices.");

	prop= RNA_def_property(srna, "lock_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Y);
	RNA_def_property_ui_text(prop, "Lock Y", "Disallow changes to the Y axis of vertices.");

	prop= RNA_def_property(srna, "lock_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Z);
	RNA_def_property_ui_text(prop, "Lock Z", "Disallow changes to the Z axis of vertices.");

	prop= RNA_def_property(srna, "show_brush", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DRAW_BRUSH);
	RNA_def_property_ui_text(prop, "Show Brush", "");

	prop= RNA_def_property(srna, "partial_redraw", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DRAW_FAST);
	RNA_def_property_ui_text(prop, "Partial Redraw", "Optimize sculpting by only refreshing modified faces.");
}

static void rna_def_vertex_paint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	static EnumPropertyItem prop_mode_items[] = {
		{0, "MIX", 0, "Mix", "Use mix blending mode while painting."},
		{1, "ADD", 0, "Add", "Use add blending mode while painting."},
		{2, "SUB", 0, "Subtract", "Use subtract blending mode while painting."},
		{3, "MUL", 0, "Multiply", "Use multiply blending mode while painting."},
		{4, "BLUR", 0, "Blur", "Blur the color with surrounding values"},
		{5, "LIGHTEN", 0, "Lighten", "Use lighten blending mode while painting."},
		{6, "DARKEN", 0, "Darken", "Use darken blending mode while painting."},
		{0, NULL, 0, NULL, NULL}};
	
	srna= RNA_def_struct(brna, "VertexPaint", "Paint");
	RNA_def_struct_sdna(srna, "VPaint");
	RNA_def_struct_ui_text(srna, "Vertex Paint", "Properties of vertex and weight paint mode.");
    
	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Brush Mode", "Mode in which color is painted.");
	
	prop= RNA_def_property(srna, "all_faces", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_AREA);
	RNA_def_property_ui_text(prop, "All Faces", "Paint on all faces inside brush.");
	
	prop= RNA_def_property(srna, "vertex_dist", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_SOFT);
	RNA_def_property_ui_text(prop, "Vertex Dist", "Use distances to vertices (instead of paint entire faces).");
	
	prop= RNA_def_property(srna, "normals", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_NORMALS);
	RNA_def_property_ui_text(prop, "Normals", "Applies the vertex normal before painting.");
	
	prop= RNA_def_property(srna, "spray", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_SPRAY);
	RNA_def_property_ui_text(prop, "Spray", "Keep applying paint effect while holding mouse.");
	
	prop= RNA_def_property(srna, "gamma", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.1f, 5.0f);
	RNA_def_property_ui_text(prop, "Gamma", "Vertex paint Gamma.");
	
	prop= RNA_def_property(srna, "mul", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.1f, 50.0f);
	RNA_def_property_ui_text(prop, "Mul", "Vertex paint Mul.");
}

static void rna_def_image_paint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem tool_items[] = {
		{PAINT_TOOL_DRAW, "DRAW", 0, "Draw", ""},
		{PAINT_TOOL_SOFTEN, "SOFTEN", 0, "Soften", ""},
		{PAINT_TOOL_SMEAR, "SMEAR", 0, "Smear", ""},
		{PAINT_TOOL_CLONE, "CLONE", 0, "Clone", ""},
		{0, NULL, 0, NULL, NULL}};
	
	srna= RNA_def_struct(brna, "ImagePaint", "Paint");
	RNA_def_struct_sdna(srna, "ImagePaintSettings");
	RNA_def_struct_ui_text(srna, "Image Paint", "Properties of image and texture painting mode.");
 
	prop= RNA_def_property(srna, "tool", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, tool_items);
	RNA_def_property_ui_text(prop, "Tool", "");

	/* booleans */

	prop= RNA_def_property(srna, "show_brush_draw", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_DRAW_TOOL);
	RNA_def_property_ui_text(prop, "Show Brush Draw", "Enables brush shape while drawing.");

	prop= RNA_def_property(srna, "show_brush", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_DRAW_TOOL_DRAWING);
	RNA_def_property_ui_text(prop, "Show Brush", "Enables brush shape while not drawing.");
		
	prop= RNA_def_property(srna, "use_projection", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_DISABLE);
	RNA_def_property_ui_text(prop, "Project Paint", "Use projection painting for improved consistency in the brush strokes.");
	
	prop= RNA_def_property(srna, "use_occlude", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_XRAY);
	RNA_def_property_ui_text(prop, "Occlude", "Only paint onto the faces directly under the brush (slower)");
	
	prop= RNA_def_property(srna, "use_backface_cull", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_BACKFACE);
	RNA_def_property_ui_text(prop, "Cull", "Ignore faces pointing away from the view (faster)");
	
	prop= RNA_def_property(srna, "use_normal_falloff", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_FLAT);
	RNA_def_property_ui_text(prop, "Normal", "Paint most on faces pointing towards the view");
	
	prop= RNA_def_property(srna, "use_stencil_layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_MASK);
	RNA_def_property_ui_text(prop, "Stencil Layer", "Set the mask layer from the UV layer buttons");
	
	prop= RNA_def_property(srna, "invert_stencil", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_MASK_INV);
	RNA_def_property_ui_text(prop, "Invert", "Invert the stencil layer");
	
	prop= RNA_def_property(srna, "use_clone_layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_CLONE);
	RNA_def_property_ui_text(prop, "Clone Layer", "Use another UV layer as clone source, otherwise use 3D the cursor as the source");
	
	/* integers */
	
	prop= RNA_def_property(srna, "seam_bleed", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_ui_range(prop, 0, 8, 0, 0);
	RNA_def_property_ui_text(prop, "Bleed", "Extend paint beyond the faces UVs to reduce seams (in pixels, slower).");

	prop= RNA_def_property(srna, "normal_angle", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_range(prop, 0, 90);
	RNA_def_property_ui_text(prop, "Angle", "Paint most on faces pointing towards the view acording to this angle.");
}

static void rna_def_particle_edit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem tool_items[] = {
		{PE_BRUSH_NONE, "NONE", 0, "None", "Don't use any brush."},
		{PE_BRUSH_COMB, "COMB", 0, "Comb", "Comb hairs."},
		{PE_BRUSH_SMOOTH, "SMOOTH", 0, "Smooth", "Smooth hairs."},
		{PE_BRUSH_WEIGHT, "WEIGHT", 0, "Weight", "Assign weight to hairs."},
		{PE_BRUSH_ADD, "ADD", 0, "Add", "Add hairs."},
		{PE_BRUSH_LENGTH, "LENGTH", 0, "Length", "Make hairs longer or shorter."},
		{PE_BRUSH_PUFF, "PUFF", 0, "Puff", "Make hairs stand up."},
		{PE_BRUSH_CUT, "CUT", 0, "Cut", "Cut hairs."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem select_mode_items[] = {
		{SCE_SELECT_PATH, "PATH", ICON_EDGESEL, "Path", ""}, // XXX icon
		{SCE_SELECT_POINT, "POINT", ICON_VERTEXSEL, "Point", ""}, // XXX icon
		{SCE_SELECT_END, "END", ICON_FACESEL, "End", "E"}, // XXX icon
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem puff_mode[] = {
		{0, "ADD", 0, "Add", "Make hairs more puffy."},
		{1, "SUB", 0, "Sub", "Make hairs less puffy."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem length_mode[] = {
		{0, "GROW", 0, "Grow", "Make hairs longer."},
		{1, "SHRINK", 0, "Shrink", "Make hairs shorter."},
		{0, NULL, 0, NULL, NULL}};

	/* edit */

	srna= RNA_def_struct(brna, "ParticleEdit", NULL);
	RNA_def_struct_sdna(srna, "ParticleEditSettings");
	RNA_def_struct_ui_text(srna, "Particle Edit", "Properties of particle editing mode.");

	prop= RNA_def_property(srna, "tool", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "brushtype");
	RNA_def_property_enum_items(prop, tool_items);
	RNA_def_property_ui_text(prop, "Tool", "");

	prop= RNA_def_property(srna, "selection_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "selectmode");
	RNA_def_property_enum_items(prop, select_mode_items);
	RNA_def_property_ui_text(prop, "Selection Mode", "Particle select and display mode.");

	prop= RNA_def_property(srna, "keep_lengths", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_KEEP_LENGTHS);
	RNA_def_property_ui_text(prop, "Keep Lengths", "Keep path lengths constant.");

	prop= RNA_def_property(srna, "keep_root", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_LOCK_FIRST);
	RNA_def_property_ui_text(prop, "Keep Root", "Keep root keys unmodified.");

	prop= RNA_def_property(srna, "emitter_deflect", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_DEFLECT_EMITTER);
	RNA_def_property_ui_text(prop, "Deflect Emitter", "Keep paths from intersecting the emitter.");

	prop= RNA_def_property(srna, "emitter_distance", PROP_FLOAT, PROP_UNSIGNED);
	RNA_def_property_float_sdna(prop, NULL, "emitterdist");
	RNA_def_property_ui_range(prop, 0.0f, 10.0f, 10, 3);
	RNA_def_property_ui_text(prop, "Emitter Distance", "Distance to keep particles away from the emitter.");

	prop= RNA_def_property(srna, "show_time", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_SHOW_TIME);
	RNA_def_property_ui_text(prop, "Show Time", "Show time values of the baked keys.");

	prop= RNA_def_property(srna, "show_children", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_SHOW_CHILD);
	RNA_def_property_ui_text(prop, "Show Children", "Show child particles.");

	prop= RNA_def_property(srna, "mirror_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_X_MIRROR);
	RNA_def_property_ui_text(prop, "X-Axis Mirror", "Mirror operations over the X axis while editing.");

	prop= RNA_def_property(srna, "add_interpolate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_INTERPOLATE_ADDED);
	RNA_def_property_ui_text(prop, "Interpolate", "Interpolate new particles from the existing ones.");

	prop= RNA_def_property(srna, "add_keys", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "totaddkey");
	RNA_def_property_range(prop, 2, INT_MAX);
	RNA_def_property_ui_range(prop, 2, 20, 10, 3);
	RNA_def_property_ui_text(prop, "Keys", "How many keys to make new particles with.");

	prop= RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ParticleBrush");
	RNA_def_property_pointer_funcs(prop, "rna_ParticleEdit_brush_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Brush", "");

	/* brush */

	srna= RNA_def_struct(brna, "ParticleBrush", NULL);
	RNA_def_struct_sdna(srna, "ParticleBrushData");
	RNA_def_struct_ui_text(srna, "Particle Brush", "Particle editing brush.");

	prop= RNA_def_property(srna, "size", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, INT_MAX);
	RNA_def_property_ui_range(prop, 1, 100, 10, 3);
	RNA_def_property_ui_text(prop, "Size", "Brush size.");

	prop= RNA_def_property(srna, "strength", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, INT_MAX);
	RNA_def_property_ui_range(prop, 1, 100, 10, 3);
	RNA_def_property_ui_text(prop, "Strength", "Brush strength.");

	prop= RNA_def_property(srna, "steps", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "step");
	RNA_def_property_range(prop, 1, INT_MAX);
	RNA_def_property_ui_range(prop, 1, 50, 10, 3);
	RNA_def_property_ui_text(prop, "Steps", "Brush steps.");

	prop= RNA_def_property(srna, "puff_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "invert");
	RNA_def_property_enum_items(prop, puff_mode);
	RNA_def_property_ui_text(prop, "Puff Mode", "");

	prop= RNA_def_property(srna, "length_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "invert");
	RNA_def_property_enum_items(prop, length_mode);
	RNA_def_property_ui_text(prop, "Length Mode", "");

	/* dummy */
	prop= RNA_def_property(srna, "curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "CurveMapping");
	RNA_def_property_pointer_funcs(prop, "rna_ParticleBrush_curve_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Curve", "");
}

void RNA_def_sculpt_paint(BlenderRNA *brna)
{
	rna_def_paint(brna);
	rna_def_sculpt(brna);
	rna_def_vertex_paint(brna);
	rna_def_image_paint(brna);
	rna_def_particle_edit(brna);
}

#endif

