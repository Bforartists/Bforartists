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
 * Contributor(s): Blender Foundation (2008), Juho Veps�l�inen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_curve_types.h"
#include "DNA_material_types.h"
#include "DNA_scene_types.h"

#include "BKE_font.h"

#include "WM_types.h"

EnumPropertyItem beztriple_handle_type_items[] = {
		{HD_FREE, "FREE", 0, "Free", ""},
		{HD_AUTO, "AUTO", 0, "Auto", ""},
		{HD_VECT, "VECTOR", 0, "Vector", ""},
		{HD_ALIGN, "ALIGNED", 0, "Aligned", ""},
		{HD_AUTO_ANIM, "AUTO_CLAMPED", 0, "Auto Clamped", ""},
		{0, NULL, 0, NULL, NULL}};

EnumPropertyItem beztriple_interpolation_mode_items[] = {
		{BEZT_IPO_CONST, "CONSTANT", 0, "Constant", ""},
		{BEZT_IPO_LIN, "LINEAR", 0, "Linear", ""},
		{BEZT_IPO_BEZ, "BEZIER", 0, "Bezier", ""},
		{0, NULL, 0, NULL, NULL}};
		
EnumPropertyItem beztriple_keyframe_type_items[] = {
		{BEZT_KEYTYPE_KEYFRAME, "KEYFRAME", 0, "Keyframe", ""},
		{BEZT_KEYTYPE_BREAKDOWN, "BREAKDOWN", 0, "Breakdown", ""},
		{BEZT_KEYTYPE_EXTREME, "EXTREME", 0, "Extreme", ""},
		{0, NULL, 0, NULL, NULL}};

#ifdef RNA_RUNTIME

#include "DNA_object_types.h"

#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_main.h"

#include "WM_api.h"

static StructRNA *rna_Curve_refine(PointerRNA *ptr)
{
	Curve *cu= (Curve*)ptr->data;
	short obtype= curve_type(cu);

	if(obtype == OB_FONT) return &RNA_TextCurve;
	else if(obtype == OB_SURF) return &RNA_SurfaceCurve;
	else return &RNA_Curve;
}


static PointerRNA rna_Curve_active_nurb_get(PointerRNA *ptr)
{
	Curve *cu= (Curve*)ptr->data;
	Nurb *nu= NULL;

	if(cu->editnurb)
		nu = BLI_findlink(cu->editnurb, cu->actnu);

	if(nu)
		return rna_pointer_inherit_refine(ptr, &RNA_Nurb, nu);

	return rna_pointer_inherit_refine(ptr, NULL, NULL);
}


static void rna_BezTriple_handle1_get(PointerRNA *ptr, float *values)
{
	BezTriple *bt= (BezTriple*)ptr->data;

	values[0]= bt->vec[0][0];
	values[1]= bt->vec[0][1];
	values[2]= bt->vec[0][2];
}

static void rna_BezTriple_handle1_set(PointerRNA *ptr, const float *values)
{
	BezTriple *bt= (BezTriple*)ptr->data;

	bt->vec[0][0]= values[0];
	bt->vec[0][1]= values[1];
	bt->vec[0][2]= values[2];
}

static void rna_BezTriple_handle2_get(PointerRNA *ptr, float *values)
{
	BezTriple *bt= (BezTriple*)ptr->data;

	values[0]= bt->vec[2][0];
	values[1]= bt->vec[2][1];
	values[2]= bt->vec[2][2];
}

static void rna_BezTriple_handle2_set(PointerRNA *ptr, const float *values)
{
	BezTriple *bt= (BezTriple*)ptr->data;

	bt->vec[2][0]= values[0];
	bt->vec[2][1]= values[1];
	bt->vec[2][2]= values[2];
}

static void rna_BezTriple_ctrlpoint_get(PointerRNA *ptr, float *values)
{
	BezTriple *bt= (BezTriple*)ptr->data;

	values[0]= bt->vec[1][0];
	values[1]= bt->vec[1][1];
	values[2]= bt->vec[1][2];
}

static void rna_BezTriple_ctrlpoint_set(PointerRNA *ptr, const float *values)
{
	BezTriple *bt= (BezTriple*)ptr->data;

	bt->vec[1][0]= values[0];
	bt->vec[1][1]= values[1];
	bt->vec[1][2]= values[2];
}

static int rna_Curve_texspace_editable(PointerRNA *ptr)
{
	Curve *cu= (Curve*)ptr->data;
	return (cu->texflag & CU_AUTOSPACE)? 0: PROP_EDITABLE;
}

static void rna_Curve_material_index_range(PointerRNA *ptr, int *min, int *max)
{
	Curve *cu= (Curve*)ptr->id.data;
	*min= 0;
	*max= cu->totcol-1;
}

static void rna_Curve_active_textbox_index_range(PointerRNA *ptr, int *min, int *max)
{
	Curve *cu= (Curve*)ptr->id.data;
	*min= 0;
	*max= cu->totbox-1;
}


static void rna_Curve_dimension_set(PointerRNA *ptr, int value)
{
	Curve *cu= (Curve*)ptr->id.data;
	Nurb *nu= cu->editnurb ? cu->editnurb->first : cu->nurb.first;

	if(value==CU_3D) {
		cu->flag |=  CU_3D;
		for( ; nu; nu= nu->next) {
			nu->flag &= ~CU_2D;
		}
	}
	else {
		cu->flag &= ~CU_3D;
		for( ; nu; nu= nu->next) {
			nu->flag |= CU_2D;
			test2DNurb(nu);

			/* since the handles are moved they need to be auto-located again */
			if(nu->type == CU_BEZIER)
				calchandlesNurb(nu);
		}
	}
}



static int rna_Nurb_length(PointerRNA *ptr)
{
	Nurb *nu= (Nurb*)ptr->data;
	return nu->pntsv>0 ? nu->pntsu*nu->pntsv : nu->pntsu;
}

static void rna_Nurb_type_set(PointerRNA *ptr, int value)
{
	Nurb *nu= (Nurb*)ptr->data;
	nu->type = value;
	// XXX - TODO change datatypes
}

static void rna_BPoint_array_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Nurb *nu= (Nurb*)ptr->data;
	rna_iterator_array_begin(iter, (void*)nu->bp, sizeof(BPoint*), nu->pntsv>0 ? nu->pntsu*nu->pntsv : nu->pntsu, 0, NULL);
}

static void rna_Curve_update_data(bContext *C, PointerRNA *ptr)
{
	ID *id= ptr->id.data;
	
	DAG_id_flush_update(id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, id);
}

static void rna_Nurb_update_handle_data(bContext *C, PointerRNA *ptr)
{
	Nurb *nu= (Nurb*)ptr->data;

	if(nu->type == CU_BEZIER)
		calchandlesNurb(nu);

	rna_Curve_update_data(C, ptr);
}

static void rna_Nurb_update_knot_u(bContext *C, PointerRNA *ptr)
{
	Nurb *nu= (Nurb*)ptr->data;

	clamp_nurb_order_u(nu);
	makeknots(nu, 1);

	rna_Curve_update_data(C, ptr);
}

static void rna_Nurb_update_knot_v(bContext *C, PointerRNA *ptr)
{
	Nurb *nu= (Nurb*)ptr->data;

	clamp_nurb_order_v(nu);
	makeknots(nu, 2);

	rna_Curve_update_data(C, ptr);
}



#else

static void rna_def_bpoint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "CurvePoint", NULL);
	RNA_def_struct_sdna(srna, "BPoint");
	RNA_def_struct_ui_text(srna, "CurvePoint", "Curve point without handles.");

	/* Boolean values */
	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "f1", 0);
	RNA_def_property_ui_text(prop, "Selected", "Selection status");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "hidden", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "hide", 0);
	RNA_def_property_ui_text(prop, "Hidden", "Visibility status");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	/* Vector value */
	prop= RNA_def_property(srna, "point", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 4);
	RNA_def_property_float_sdna(prop, NULL, "vec");
	RNA_def_property_ui_text(prop, "Point", "Point coordinates");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	/* Number values */
	prop= RNA_def_property(srna, "tilt", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "alfa");
	/*RNA_def_property_range(prop, -FLT_MAX, FLT_MAX);*/
	RNA_def_property_ui_text(prop, "Tilt", "Tilt in 3d View");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.01f, 100.0f);
	RNA_def_property_ui_text(prop, "Weight", "Softbody goal weight");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "radius", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "radius");
	/*RNA_def_property_range(prop, 0.0f, 1.0f);*/
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bevel Radius", "Radius for bevelling");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_beztriple(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "BezierCurvePoint", NULL);
	RNA_def_struct_sdna(srna, "BezTriple");
	RNA_def_struct_ui_text(srna, "Bezier Curve Point", "Bezier curve point with two handles.");

	/* Boolean values */
	prop= RNA_def_property(srna, "selected_handle1", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "f1", 0);
	RNA_def_property_ui_text(prop, "Handle 1 selected", "Handle 1 selection status");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "selected_handle2", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "f3", 0);
	RNA_def_property_ui_text(prop, "Handle 2 selected", "Handle 2 selection status");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "selected_control_point", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "f2", 0);
	RNA_def_property_ui_text(prop, "Control Point selected", "Control point selection status");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "hidden", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "hide", 0);
	RNA_def_property_ui_text(prop, "Hidden", "Visibility status");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	/* Enums */
	prop= RNA_def_property(srna, "handle1_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "h1");
	RNA_def_property_enum_items(prop, beztriple_handle_type_items);
	RNA_def_property_ui_text(prop, "Handle 1 Type", "Handle types");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "handle2_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "h2");
	RNA_def_property_enum_items(prop, beztriple_handle_type_items);
	RNA_def_property_ui_text(prop, "Handle 2 Type", "Handle types");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "interpolation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "ipo");
	RNA_def_property_enum_items(prop, beztriple_interpolation_mode_items);
	RNA_def_property_ui_text(prop, "Interpolation", "(For F-Curves Only) Interpolation to use for segment of curve starting from current BezTriple.");
	//RNA_def_property_update(prop, 0, "rna_Curve_update_data"); // this should be an F-Curve update call instead...
	
	prop= RNA_def_property(srna, "keyframe_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "hide");
	RNA_def_property_enum_items(prop, beztriple_keyframe_type_items);
	RNA_def_property_ui_text(prop, "Keyframe Type", "(For F-Curves only) The type of keyframe this control point defines.");
	//RNA_def_property_update(prop, 0, "rna_Curve_update_data"); // this should be an F-Curve update call instead...

	/* Vector values */
	prop= RNA_def_property(srna, "handle1", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 3);
	RNA_def_property_float_funcs(prop, "rna_BezTriple_handle1_get", "rna_BezTriple_handle1_set", NULL);
	RNA_def_property_ui_text(prop, "Handle 1", "Coordinates of the first handle");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "control_point", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 3);
	RNA_def_property_float_funcs(prop, "rna_BezTriple_ctrlpoint_get", "rna_BezTriple_ctrlpoint_set", NULL);
	RNA_def_property_ui_text(prop, "Control Point", "Coordinates of the control point");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "handle2", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 3);
	RNA_def_property_float_funcs(prop, "rna_BezTriple_handle2_get", "rna_BezTriple_handle2_set", NULL);
	RNA_def_property_ui_text(prop, "Handle 2", "Coordinates of the second handle");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	/* Number values */
	prop= RNA_def_property(srna, "tilt", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "alfa");
	/*RNA_def_property_range(prop, -FLT_MAX, FLT_MAX);*/
	RNA_def_property_ui_text(prop, "Tilt", "Tilt in 3d View");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.01f, 100.0f);
	RNA_def_property_ui_text(prop, "Weight", "Softbody goal weight");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "radius", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "radius");
	/*RNA_def_property_range(prop, 0.0f, 1.0f);*/
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bevel Radius", "Radius for bevelling");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_path(BlenderRNA *brna, StructRNA *srna)
{
	PropertyRNA *prop;
	
	/* number values */
	prop= RNA_def_property(srna, "path_length", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "pathlen");
	RNA_def_property_range(prop, 1, 32767);
	RNA_def_property_ui_text(prop, "Path Length", "If no speed IPO was set, the length of path in frames.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	/* flags */
	prop= RNA_def_property(srna, "use_path", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_PATH);
	RNA_def_property_ui_text(prop, "Path", "Enable the curve to become a translation path.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "use_path_follow", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_FOLLOW);
	RNA_def_property_ui_text(prop, "Follow", "Make curve path children to rotate along the path.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "use_stretch", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_STRETCH);
	RNA_def_property_ui_text(prop, "Stretch", "Option for curve-deform: makes deformed child to stretch along entire path.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "use_time_offset", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_OFFS_PATHDIST);
	RNA_def_property_ui_text(prop, "Offset Path Distance", "Children will use TimeOffs value as path distance offset.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "use_radius", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_PATH_RADIUS);
	RNA_def_property_ui_text(prop, "Radius", "Option for paths: apply the curve radius with path following it and deforming.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_nurbs(BlenderRNA *brna, StructRNA *srna)
{
	PropertyRNA *prop;
	
	/* flags */
	prop= RNA_def_property(srna, "uv_orco", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_UV_ORCO);
	RNA_def_property_ui_text(prop, "UV Orco", "Forces to use UV coordinates for texture mapping 'orco'.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "vertex_normal_flip", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", CU_NOPUNOFLIP);
	RNA_def_property_ui_text(prop, "Vertex Normal Flip", "Flip vertex normals towards the camera during render");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_font(BlenderRNA *brna, StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem prop_align_items[] = {
		{CU_LEFT, "LEFT", 0, "Left", "Align text to the left"},
		{CU_MIDDLE, "CENTRAL", 0, "Center", "Center text"},
		{CU_RIGHT, "RIGHT", 0, "Right", "Align text to the right"},
		{CU_JUSTIFY, "JUSTIFY", 0, "Justify", "Align to the left and the right"},
		{CU_FLUSH, "FLUSH", 0, "Flush", "Align to the left and the right, with equal character spacing"},
		{0, NULL, 0, NULL, NULL}};
		
	/* Enums */
	prop= RNA_def_property(srna, "spacemode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_align_items);
	RNA_def_property_ui_text(prop, "Text Align", "Text align from the object center.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	/* number values */
	prop= RNA_def_property(srna, "text_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fsize");
	RNA_def_property_range(prop, 0.1f, 10.0f);
	RNA_def_property_ui_text(prop, "Font size", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "line_dist", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "linedist");
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Distance between lines of text", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "word_spacing", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "wordspace");
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Spacing between words", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "spacing", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "spacing");
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Global spacing between characters", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "shear", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "shear");
	RNA_def_property_range(prop, -1.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Shear", "Italic angle of the characters");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "offset_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xof");
	RNA_def_property_range(prop, -50.0f, 50.0f);
	RNA_def_property_ui_text(prop, "X Offset", "Horizontal offset from the object center");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "offset_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "yof");
	RNA_def_property_range(prop, -50.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Y Offset", "Vertical offset from the object center");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "ul_position", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ulpos");
	RNA_def_property_range(prop, -0.2f, 0.8f);
	RNA_def_property_ui_text(prop, "Underline Position", "Vertical position of underline");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "ul_height", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ulheight");
	RNA_def_property_range(prop, -0.2f, 0.8f);
	RNA_def_property_ui_text(prop, "Underline Thickness", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "textboxes", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "tb", "totbox");
	RNA_def_property_struct_type(prop, "TextBox");
	RNA_def_property_ui_text(prop, "Textboxes", "");

	prop= RNA_def_property(srna, "active_textbox", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "actbox");
	RNA_def_property_ui_text(prop, "The active text box", "");
	RNA_def_property_int_funcs(prop, NULL, NULL, "rna_Curve_active_textbox_index_range");
	
	/* strings */
	prop= RNA_def_property(srna, "family", PROP_STRING, PROP_NONE);
	RNA_def_property_string_maxlength(prop, 21);
	RNA_def_property_ui_text(prop, "Object Font", "Use Blender Objects as font characters. Give font objects a common name followed by the character it represents, eg. familya, familyb etc, and turn on Verts Duplication");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "str", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "str");
	RNA_def_property_ui_text(prop, "String", "");
	RNA_def_property_string_funcs(prop, "rna_ID_name_get", "rna_ID_name_length", "rna_ID_name_set");
	RNA_def_property_string_maxlength(prop, 8192); /* note that originally str did not have a limit! */
	RNA_def_struct_name_property(srna, prop);
	
	/* pointers */
	prop= RNA_def_property(srna, "text_on_curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "textoncurve");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Text on Curve", "Curve deforming text object.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "font", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "vfont");
	RNA_def_property_ui_text(prop, "Font", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "edit_format", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "curinfo");
	RNA_def_property_ui_text(prop, "Edit Format", "Editing settings character formatting.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	/* flags */
	prop= RNA_def_property(srna, "fast", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_FAST);
	RNA_def_property_ui_text(prop, "Fast", "Don't fill polygons while editing.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_textbox(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "TextBox", NULL);
	RNA_def_struct_ui_text(srna, "Text Box", "Text bounding box for layout.");
	
	/* number values */
	prop= RNA_def_property(srna, "x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "x");
	RNA_def_property_range(prop, -50.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Textbox X Offset", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "y");
	RNA_def_property_range(prop, -50.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Textbox Y Offset", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "width", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "w");
	RNA_def_property_range(prop, 0.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Textbox Width", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "height", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "h");
	RNA_def_property_range(prop, 0.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Textbox Height", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_charinfo(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "TextCharacterFormat", NULL);
	RNA_def_struct_sdna(srna, "CharInfo");
	RNA_def_struct_ui_text(srna, "Text Character Format", "Text character formatting settings.");
	
	/* flags */
	prop= RNA_def_property(srna, "style", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_STYLE);
	RNA_def_property_ui_text(prop, "Style", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "bold", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_BOLD);
	RNA_def_property_ui_text(prop, "Bold", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "italic", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_ITALIC);
	RNA_def_property_ui_text(prop, "Italic", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "underline", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_UNDERLINE);
	RNA_def_property_ui_text(prop, "Underline", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "wrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_WRAP);
	RNA_def_property_ui_text(prop, "Wrap", "");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_surface(BlenderRNA *brna)
{
	StructRNA *srna;
	
	srna= RNA_def_struct(brna, "SurfaceCurve", "Curve");
	RNA_def_struct_sdna(srna, "Curve");
	RNA_def_struct_ui_text(srna, "Surface Curve", "Curve datablock used for storing surfaces.");
	RNA_def_struct_ui_icon(srna, ICON_SURFACE_DATA);

	rna_def_nurbs(brna, srna);
}

static void rna_def_text(BlenderRNA *brna)
{
	StructRNA *srna;
	
	srna= RNA_def_struct(brna, "TextCurve", "Curve");
	RNA_def_struct_sdna(srna, "Curve");
	RNA_def_struct_ui_text(srna, "Text Curve", "Curve datablock used for storing text.");
	RNA_def_struct_ui_icon(srna, ICON_FONT_DATA);

	rna_def_font(brna, srna);
	rna_def_nurbs(brna, srna);
}

static void rna_def_curve(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem curve_twist_mode_items[] = {
			{CU_TWIST_Z_UP, "Z_UP", 0, "Z-Up", "Use Z-Up axis to calculate the curve twist at each point"},
			{CU_TWIST_MINIMUM, "MINIMUM", 0, "Minimum", "Use the least twist over the entire curve"},
			{CU_TWIST_TANGENT, "TANGENT", 0, "Tangent", "Use the tangent to calculate twist"},
			{0, NULL, 0, NULL, NULL}};

	static const EnumPropertyItem curve_axis_items[]= {
		{0, "2D", 0, "2D", "Clamp the Z axis of of the curve"},
		{CU_3D, "3D", 0, "3D", "Allow editing on the Z axis of this curve, also alows tilt and curve radius to be used."},
		{0, NULL, 0, NULL, NULL}};
			
	srna= RNA_def_struct(brna, "Curve", "ID");
	RNA_def_struct_ui_text(srna, "Curve", "Curve datablock storing curves, splines and NURBS.");
	RNA_def_struct_ui_icon(srna, ICON_CURVE_DATA);
	RNA_def_struct_refine_func(srna, "rna_Curve_refine");
	
	rna_def_animdata_common(srna);
	rna_def_texmat_common(srna, "rna_Curve_texspace_editable");

	prop= RNA_def_property(srna, "shape_keys", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "key");
	RNA_def_property_ui_text(prop, "Shape Keys", "");

	prop= RNA_def_property(srna, "splines", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "nurb", NULL);
	RNA_def_property_struct_type(prop, "Nurb");
	RNA_def_property_ui_text(prop, "Splines", "Collection of splines in this curve data object.");

	prop= RNA_def_property(srna, "active_spline", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Nurb");
	RNA_def_property_pointer_funcs(prop, "rna_Curve_active_nurb_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Active Spline", "The active editmode spline");


	prop= RNA_def_property(srna, "draw_handles", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "drawflag", CU_HIDE_HANDLES);
	RNA_def_property_ui_text(prop, "Draw Handles", "Display bezier handles in editmode.");
	RNA_def_property_update(prop, NC_GEOM|ND_DATA, NULL);

	prop= RNA_def_property(srna, "draw_normals", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "drawflag", CU_HIDE_NORMALS);
	RNA_def_property_ui_text(prop, "Draw Normals", "Display 3D curve normals in editmode.");
	RNA_def_property_update(prop, NC_GEOM|ND_DATA, NULL);

	rna_def_path(brna, srna);
	
	/* Number values */
	prop= RNA_def_property(srna, "bevel_resolution", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "bevresol");
	RNA_def_property_range(prop, 0, 32);
	RNA_def_property_ui_range(prop, 0, 32, 1.0, 0);
	RNA_def_property_ui_text(prop, "Bevel Resolution", "Bevel resolution when depth is non-zero and no specific bevel object has been defined.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "width", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "width");
	RNA_def_property_ui_range(prop, 0, 2.0, 0.1, 0);
	RNA_def_property_ui_text(prop, "Width", "Scale the original width (1.0) based on given factor.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "extrude", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ext1");
	RNA_def_property_ui_range(prop, 0, 100.0, 0.1, 0);
	RNA_def_property_ui_text(prop, "Extrude", "Amount of curve extrusion when not using a bevel object.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "bevel_depth", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ext2");
	RNA_def_property_ui_range(prop, 0, 100.0, 0.1, 0);
	RNA_def_property_ui_text(prop, "Bevel Depth", "Bevel depth when not using a bevel object.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "resolution_u", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "resolu");
	RNA_def_property_ui_range(prop, 1, 1024, 1, 0);
	RNA_def_property_ui_text(prop, "Resolution U", "Surface resolution in U direction.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "resolution_v", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "resolv");
	RNA_def_property_ui_range(prop, 1, 1024, 1, 0);
	RNA_def_property_ui_text(prop, "Resolution V", "Surface resolution in V direction.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "render_resolution_u", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "resolu_ren");
	RNA_def_property_ui_range(prop, 1, 1024, 1, 0);
	RNA_def_property_ui_text(prop, "Render Resolution U", "Surface resolution in U direction used while rendering. Zero skips this property.");
	
	prop= RNA_def_property(srna, "render_resolution_v", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "resolv_ren");
	RNA_def_property_ui_range(prop, 1, 1024, 1, 0);
	RNA_def_property_ui_text(prop, "Render Resolution V", "Surface resolution in V direction used while rendering. Zero skips this property.");
	
	
	prop= RNA_def_property(srna, "eval_time", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ctime");
	RNA_def_property_ui_text(prop, "Evaluation Time", "Parametric position along the length of the curve that Objects 'following' it should be at.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	/* pointers */
	prop= RNA_def_property(srna, "bevel_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "bevobj");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bevel Object", "Curve object name that defines the bevel shape.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "taper_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "taperobj");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Taper Object", "Curve object name that defines the taper (width).");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	/* Flags */

	prop= RNA_def_property(srna, "dimensions", PROP_ENUM, PROP_NONE); /* as an enum */
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "flag");
	RNA_def_property_enum_items(prop, curve_axis_items);
	RNA_def_property_enum_funcs(prop, NULL, "rna_Curve_dimension_set", NULL);
	RNA_def_property_ui_text(prop, "Dimensions", "Select 2D or 3D curve type.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "front", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_FRONT);
	RNA_def_property_ui_text(prop, "Front", "Draw filled front for extruded/beveled curves.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "back", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_BACK);
	RNA_def_property_ui_text(prop, "Back", "Draw filled back for extruded/beveled curves.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "twist_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "twist_mode");
	RNA_def_property_enum_items(prop, curve_twist_mode_items);
	RNA_def_property_ui_text(prop, "Twist Method", "The type of tilt calculation for 3D Curves.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	// XXX - would be nice to have a better way to do this, only add for testing.
	prop= RNA_def_property(srna, "twist_smooth", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "twist_smooth");
	RNA_def_property_ui_range(prop, 0, 100.0, 0.1, 0);
	RNA_def_property_ui_text(prop, "Twist Smooth", "Smoothing iteration for tangents");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");



	prop= RNA_def_property(srna, "retopo", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_RETOPO);
	RNA_def_property_ui_text(prop, "Retopo", "Turn on the re-topology tool.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

static void rna_def_curve_nurb(BlenderRNA *brna)
{
	static EnumPropertyItem curve_type_items[] = {
		{CU_POLY, "POLY", 0, "Poly", ""},
		{CU_BEZIER, "BEZIER", 0, "Bezier", ""},
		{CU_BSPLINE, "BSPLINE", 0, "BSpline", ""},
		{CU_CARDINAL, "CARDINAL", 0, "Cardinal", ""},
		{CU_NURBS, "NURBS", 0, "Ease", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem spline_interpolation_items[] = {
		{BEZT_IPO_CONST, "LINEAR", 0, "Linear", ""},
		{BEZT_IPO_LIN, "CARDINAL", 0, "Cardinal", ""},
		{BEZT_IPO_BEZ, "BSPLINE", 0, "BSpline", ""},
		{BEZT_IPO_BEZ, "EASE", 0, "Ease", ""},
		{0, NULL, 0, NULL, NULL}};

	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Nurb", NULL);
	RNA_def_struct_ui_text(srna, "Spline", "Element of a curve, either Nurbs, Bezier or Polyline or a character with text objects.");

	prop= RNA_def_property(srna, "points", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "bp", NULL);
	RNA_def_property_struct_type(prop, "CurvePoint");
	RNA_def_property_collection_funcs(prop, "rna_BPoint_array_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", "rna_Nurb_length", 0, 0, 0, 0);
	RNA_def_property_ui_text(prop, "Points", "Collection of points that make up this poly or nurbs spline.");

	prop= RNA_def_property(srna, "bezier_points", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "BezierCurvePoint");
	RNA_def_property_collection_sdna(prop, NULL, "bezt", "pntsu");
	RNA_def_property_ui_text(prop, "Bezier Points", "Collection of points for bezier curves only.");

	
	prop= RNA_def_property(srna, "tilt_interpolation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "tilt_interp");
	RNA_def_property_enum_items(prop, spline_interpolation_items);
	RNA_def_property_ui_text(prop, "Tilt Interpolation", "The type of tilt interpolation for 3D, Bezier curves.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "radius_interpolation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "radius_interp");
	RNA_def_property_enum_items(prop, spline_interpolation_items);
	RNA_def_property_ui_text(prop, "Radius Interpolation", "The type of radius interpolation for Bezier curves.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	// XXX - switching type probably needs comprehensive recalc of data like in 2.4x
	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, curve_type_items);
	RNA_def_property_enum_funcs(prop, NULL, "rna_Nurb_type_set", NULL);
	RNA_def_property_ui_text(prop, "Type", "The interpolation type for this curve element.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "point_count_u", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); /* editing this needs knot recalc*/
	RNA_def_property_int_sdna(prop, NULL, "pntsu");
	RNA_def_property_ui_text(prop, "Points U", "Total number points for the curve or surface in the U direction");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "point_count_v", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); /* editing this needs knot recalc*/
	RNA_def_property_int_sdna(prop, NULL, "pntsv");
	RNA_def_property_ui_text(prop, "Points V", "Total number points for the surface on the V direction");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");


	prop= RNA_def_property(srna, "order_u", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "orderu");
	RNA_def_property_range(prop, 2, 6);
	RNA_def_property_ui_text(prop, "Order U", "Nurbs order in the U direction (For splines and surfaces), Higher values let points influence a greater area");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_knot_u");

	prop= RNA_def_property(srna, "order_v", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "orderv");
	RNA_def_property_range(prop, 2, 6);
	RNA_def_property_ui_text(prop, "Order V", "Nurbs order in the V direction (For surfaces only), Higher values let points influence a greater area");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_knot_v");


	prop= RNA_def_property(srna, "resolution_u", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "resolu");
	RNA_def_property_range(prop, 1, 1024);
	RNA_def_property_ui_text(prop, "Resolution U", "Curve or Surface subdivisions per segment");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "resolution_v", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "resolv");
	RNA_def_property_range(prop, 1, 1024);
	RNA_def_property_ui_text(prop, "Resolution V", "Surface subdivisions per segment");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "cyclic_u", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flagu", CU_CYCLIC);
	RNA_def_property_ui_text(prop, "Cyclic U", "Make this curve or surface a closed loop in the U direction.");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_handle_data"); /* only needed for cyclic_u because cyclic_v cant do bezier */

	prop= RNA_def_property(srna, "cyclic_v", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flagv", CU_CYCLIC);
	RNA_def_property_ui_text(prop, "Cyclic V", "Make this surface a closed loop in the V direction.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");


	/* Note, endpoint and bezier flags should never be on at the same time! */
	prop= RNA_def_property(srna, "endpoint_u", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flagu", 2);
	RNA_def_property_ui_text(prop, "Endpoint U", "Make this nurbs curve or surface meet the endpoints in the U direction (Cyclic U must be disabled).");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_knot_u");

	prop= RNA_def_property(srna, "endpoint_v", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flagv", 2);
	RNA_def_property_ui_text(prop, "Endpoint V", "Make this nurbs surface meet the endpoints in the V direction (Cyclic V must be disabled).");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_knot_v");

	prop= RNA_def_property(srna, "bezier_u", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flagu", 4);
	RNA_def_property_ui_text(prop, "Bezier U", "Make this nurbs curve or surface act like a bezier spline in the U direction (Order U must be 3 or 4, Cyclic U must be disabled).");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_knot_u");

	prop= RNA_def_property(srna, "bezier_v", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flagv", 4);
	RNA_def_property_ui_text(prop, "Bezier V", "Make this nurbs surface act like a bezier spline in the V direction (Order V must be 3 or 4, Cyclic V must be disabled).");
	RNA_def_property_update(prop, 0, "rna_Nurb_update_knot_v");


	prop= RNA_def_property(srna, "smooth", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CU_SMOOTH);
	RNA_def_property_ui_text(prop, "Smooth", "Smooth the normals of the surface or beveled curve.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "hide", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "hide", 1);
	RNA_def_property_ui_text(prop, "Hide", "Hide this curve in editmode.");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");

	prop= RNA_def_property(srna, "material_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "mat_nr");
	RNA_def_property_ui_text(prop, "Material Index", "");
	RNA_def_property_int_funcs(prop, NULL, NULL, "rna_Curve_material_index_range");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
	
	prop= RNA_def_property(srna, "character_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "charidx");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); /* editing this needs knot recalc*/
	RNA_def_property_ui_text(prop, "Character Index", "Location of this character in the text data (only for text curves)");
	RNA_def_property_update(prop, 0, "rna_Curve_update_data");
}

void RNA_def_curve(BlenderRNA *brna)
{
	rna_def_curve(brna);
	rna_def_surface(brna);
	rna_def_text(brna);
	rna_def_textbox(brna);
	rna_def_charinfo(brna);
	rna_def_bpoint(brna);
	rna_def_beztriple(brna);
	rna_def_curve_nurb(brna);
}

#endif

