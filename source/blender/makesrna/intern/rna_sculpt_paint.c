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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/makesrna/intern/rna_sculpt_paint.c
 *  \ingroup RNA
 */


#include <stdlib.h>

#include "RNA_define.h"

#include "rna_internal.h"

#include "DNA_ID.h"
#include "DNA_scene_types.h"
#include "DNA_brush_types.h"

#include "BKE_paint.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BLI_utildefines.h"
#include "bmesh.h"

static EnumPropertyItem particle_edit_hair_brush_items[] = {
	{PE_BRUSH_NONE, "NONE", 0, "None", "Don't use any brush"},
	{PE_BRUSH_COMB, "COMB", 0, "Comb", "Comb hairs"},
	{PE_BRUSH_SMOOTH, "SMOOTH", 0, "Smooth", "Smooth hairs"},
	{PE_BRUSH_ADD, "ADD", 0, "Add", "Add hairs"},
	{PE_BRUSH_LENGTH, "LENGTH", 0, "Length", "Make hairs longer or shorter"},
	{PE_BRUSH_PUFF, "PUFF", 0, "Puff", "Make hairs stand up"},
	{PE_BRUSH_CUT, "CUT", 0, "Cut", "Cut hairs"},
	{PE_BRUSH_WEIGHT, "WEIGHT", 0, "Weight", "Weight hair particles"},
	{0, NULL, 0, NULL, NULL}
};

EnumPropertyItem symmetrize_direction_items[] = {
	{BMO_SYMMETRIZE_NEGATIVE_X, "NEGATIVE_X", 0, "-X to +X", ""},
	{BMO_SYMMETRIZE_POSITIVE_X, "POSITIVE_X", 0, "+X to -X", ""},

	{BMO_SYMMETRIZE_NEGATIVE_Y, "NEGATIVE_Y", 0, "-Y to +Y", ""},
	{BMO_SYMMETRIZE_POSITIVE_Y, "POSITIVE_Y", 0, "+Y to -Y", ""},

	{BMO_SYMMETRIZE_NEGATIVE_Z, "NEGATIVE_Z", 0, "-Z to +Z", ""},
	{BMO_SYMMETRIZE_POSITIVE_Z, "POSITIVE_Z", 0, "+Z to -Z", ""},
	{0, NULL, 0, NULL, NULL},
};

#ifdef RNA_RUNTIME
#include "MEM_guardedalloc.h"

#include "BKE_context.h"
#include "BKE_pointcache.h"
#include "BKE_particle.h"
#include "BKE_depsgraph.h"
#include "BKE_pbvh.h"

#include "ED_particle.h"

static EnumPropertyItem particle_edit_disconnected_hair_brush_items[] = {
	{PE_BRUSH_NONE, "NONE", 0, "None", "Don't use any brush"},
	{PE_BRUSH_COMB, "COMB", 0, "Comb", "Comb hairs"},
	{PE_BRUSH_SMOOTH, "SMOOTH", 0, "Smooth", "Smooth hairs"},
	{PE_BRUSH_LENGTH, "LENGTH", 0, "Length", "Make hairs longer or shorter"},
	{PE_BRUSH_CUT, "CUT", 0, "Cut", "Cut hairs"},
	{PE_BRUSH_WEIGHT, "WEIGHT", 0, "Weight", "Weight hair particles"},
	{0, NULL, 0, NULL, NULL}
};

static EnumPropertyItem particle_edit_cache_brush_items[] = {
	{PE_BRUSH_NONE, "NONE", 0, "None", "Don't use any brush"},
	{PE_BRUSH_COMB, "COMB", 0, "Comb", "Comb paths"},
	{PE_BRUSH_SMOOTH, "SMOOTH", 0, "Smooth", "Smooth paths"},
	{PE_BRUSH_LENGTH, "LENGTH", 0, "Length", "Make paths longer or shorter"},
	{0, NULL, 0, NULL, NULL}
};

static PointerRNA rna_ParticleEdit_brush_get(PointerRNA *ptr)
{
	ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;
	ParticleBrushData *brush = NULL;

	if (pset->brushtype != PE_BRUSH_NONE)
		brush = &pset->brush[pset->brushtype];

	return rna_pointer_inherit_refine(ptr, &RNA_ParticleBrush, brush);
}

static PointerRNA rna_ParticleBrush_curve_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_CurveMapping, NULL);
}

static void rna_ParticleEdit_redo(Main *UNUSED(bmain), Scene *scene, PointerRNA *UNUSED(ptr))
{
	Object *ob = (scene->basact) ? scene->basact->object : NULL;
	PTCacheEdit *edit = PE_get_current(scene, ob);

	if (!edit)
		return;

	psys_free_path_cache(edit->psys, edit);
}

static void rna_ParticleEdit_update(Main *UNUSED(bmain), Scene *scene, PointerRNA *UNUSED(ptr))
{
	Object *ob = (scene->basact) ? scene->basact->object : NULL;

	if (ob) DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
}
static void rna_ParticleEdit_tool_set(PointerRNA *ptr, int value)
{
	ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;
	
	/* redraw hair completely if weight brush is/was used */
	if ((pset->brushtype == PE_BRUSH_WEIGHT || value == PE_BRUSH_WEIGHT) && pset->scene) {
		Object *ob = (pset->scene->basact) ? pset->scene->basact->object : NULL;
		if (ob) {
			DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
			WM_main_add_notifier(NC_OBJECT | ND_PARTICLE | NA_EDITED, NULL);
		}
	}

	pset->brushtype = value;
}
static EnumPropertyItem *rna_ParticleEdit_tool_itemf(bContext *C, PointerRNA *UNUSED(ptr),
                                                     PropertyRNA *UNUSED(prop), int *UNUSED(free))
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = (scene->basact) ? scene->basact->object : NULL;
#if 0
	PTCacheEdit *edit = PE_get_current(scene, ob);
	ParticleSystem *psys = edit ? edit->psys : NULL;
#else
	/* use this rather than PE_get_current() - because the editing cache is
	 * dependent on the cache being updated which can happen after this UI
	 * draws causing a glitch [#28883] */
	ParticleSystem *psys = psys_get_current(ob);
#endif

	if (psys) {
		if (psys->flag & PSYS_GLOBAL_HAIR) {
			return particle_edit_disconnected_hair_brush_items;
		}
		else {
			return particle_edit_hair_brush_items;
		}
	}

	return particle_edit_cache_brush_items;
}

static int rna_ParticleEdit_editable_get(PointerRNA *ptr)
{
	ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;

	return (pset->object && pset->scene && PE_get_current(pset->scene, pset->object));
}
static int rna_ParticleEdit_hair_get(PointerRNA *ptr)
{
	ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;

	if (pset->scene) {
		PTCacheEdit *edit = PE_get_current(pset->scene, pset->object);

		return (edit && edit->psys);
	}
	
	return 0;
}

static char *rna_ParticleEdit_path(PointerRNA *ptr)
{
	return BLI_strdup("tool_settings.particle_edit");
}

static int rna_Brush_mode_poll(PointerRNA *ptr, PointerRNA value)
{
	Scene *scene = (Scene *)ptr->id.data;
	ToolSettings *ts = scene->toolsettings;
	Brush *brush = value.id.data;
	int mode = 0;

	/* check the origin of the Paint struct to see which paint
	 * mode to select from */

	if (ptr->data == &ts->imapaint)
		mode = OB_MODE_TEXTURE_PAINT;
	else if (ptr->data == ts->sculpt)
		mode = OB_MODE_SCULPT;
	else if (ptr->data == ts->vpaint)
		mode = OB_MODE_VERTEX_PAINT;
	else if (ptr->data == ts->wpaint)
		mode = OB_MODE_WEIGHT_PAINT;

	return brush->ob_mode & mode;
}

static void rna_Sculpt_update(Main *UNUSED(bmain), Scene *scene, PointerRNA *UNUSED(ptr))
{
	Object *ob = (scene->basact) ? scene->basact->object : NULL;

	if (ob) {
		DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
		WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, ob);

		if (ob->sculpt) {
			ob->sculpt->bm_smooth_shading = (scene->toolsettings->sculpt->flags &
			                                 SCULPT_DYNTOPO_SMOOTH_SHADING);
		}
	}
}

static void rna_Sculpt_ShowDiffuseColor_update(Main *UNUSED(bmain), Scene *scene, PointerRNA *UNUSED(ptr))
{
	Object *ob = (scene->basact) ? scene->basact->object : NULL;

	if (ob) {
		Sculpt *sd = scene->toolsettings->sculpt;
		ob->sculpt->show_diffuse_color = sd->flags & SCULPT_SHOW_DIFFUSE;

		if (ob->sculpt->pbvh)
			pbvh_show_diffuse_color_set(ob->sculpt->pbvh, ob->sculpt->show_diffuse_color);

		WM_main_add_notifier(NC_OBJECT | ND_DRAW, ob);
	}
}

static char *rna_Sculpt_path(PointerRNA *ptr)
{
	return BLI_strdup("tool_settings.sculpt");
}

static char *rna_VertexPaint_path(PointerRNA *ptr)
{
	Scene *scene = (Scene *)ptr->id.data;
	ToolSettings *ts = scene->toolsettings;
	if (ptr->data == ts->vpaint) {
		return BLI_strdup("tool_settings.vertex_paint");
	}
	else {
		return BLI_strdup("tool_settings.weight_paint");
	}
}

static char *rna_ImagePaintSettings_path(PointerRNA *ptr)
{
	return BLI_strdup("tool_settings.image_paint");
}

static char *rna_UvSculpt_path(PointerRNA *ptr)
{
	return BLI_strdup("tool_settings.uv_sculpt");
}

#else

static void rna_def_paint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "Paint", NULL);
	RNA_def_struct_ui_text(srna, "Paint", "");

	/* Global Settings */
	prop = RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_pointer_funcs(prop, NULL, NULL, NULL, "rna_Brush_mode_poll");
	RNA_def_property_ui_text(prop, "Brush", "Active Brush");
	RNA_def_property_update(prop, NC_BRUSH | NA_EDITED, NULL);

	prop = RNA_def_property(srna, "show_brush", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_SHOW_BRUSH);
	RNA_def_property_ui_text(prop, "Show Brush", "");

	prop = RNA_def_property(srna, "show_brush_on_surface", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_SHOW_BRUSH_ON_SURFACE);
	RNA_def_property_ui_text(prop, "Show Brush On Surface", "");

	prop = RNA_def_property(srna, "show_low_resolution", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_FAST_NAVIGATE);
	RNA_def_property_ui_text(prop, "Fast Navigate", "For multires, show low resolution while navigating the view");

	prop = RNA_def_property(srna, "input_samples", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "num_input_samples");
	RNA_def_property_ui_range(prop, 1, PAINT_MAX_INPUT_SAMPLES, 0, 0);
	RNA_def_property_ui_text(prop, "Input Samples", "Average multiple input samples together to smooth the brush stroke");
}

static void rna_def_sculpt(BlenderRNA  *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "Sculpt", "Paint");
	RNA_def_struct_path_func(srna, "rna_Sculpt_path");
	RNA_def_struct_ui_text(srna, "Sculpt", "");

	prop = RNA_def_property(srna, "radial_symmetry", PROP_INT, PROP_XYZ);
	RNA_def_property_int_sdna(prop, NULL, "radial_symm");
	RNA_def_property_int_default(prop, 1);
	RNA_def_property_range(prop, 1, 64);
	RNA_def_property_ui_range(prop, 0, 32, 1, 1);
	RNA_def_property_ui_text(prop, "Radial Symmetry Count X Axis",
	                         "Number of times to copy strokes across the surface");

	prop = RNA_def_property(srna, "use_symmetry_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_X);
	RNA_def_property_ui_text(prop, "Symmetry X", "Mirror brush across the X axis");

	prop = RNA_def_property(srna, "use_symmetry_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_Y);
	RNA_def_property_ui_text(prop, "Symmetry Y", "Mirror brush across the Y axis");

	prop = RNA_def_property(srna, "use_symmetry_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_Z);
	RNA_def_property_ui_text(prop, "Symmetry Z", "Mirror brush across the Z axis");

	prop = RNA_def_property(srna, "lock_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_X);
	RNA_def_property_ui_text(prop, "Lock X", "Disallow changes to the X axis of vertices");

	prop = RNA_def_property(srna, "lock_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Y);
	RNA_def_property_ui_text(prop, "Lock Y", "Disallow changes to the Y axis of vertices");

	prop = RNA_def_property(srna, "lock_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Z);
	RNA_def_property_ui_text(prop, "Lock Z", "Disallow changes to the Z axis of vertices");

	prop = RNA_def_property(srna, "use_symmetry_feather", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMMETRY_FEATHER);
	RNA_def_property_ui_text(prop, "Symmetry Feathering",
	                         "Reduce the strength of the brush where it overlaps symmetrical daubs");

	prop = RNA_def_property(srna, "use_threaded", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_USE_OPENMP);
	RNA_def_property_ui_text(prop, "Use OpenMP",
	                         "Take advantage of multiple CPU cores to improve sculpting performance");

	prop = RNA_def_property(srna, "use_deform_only", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_ONLY_DEFORM);
	RNA_def_property_ui_text(prop, "Use Deform Only",
	                         "Use only deformation modifiers (temporary disable all "
	                         "constructive modifiers except multi-resolution)");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_update");

	prop = RNA_def_property(srna, "show_diffuse_color", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SHOW_DIFFUSE);
	RNA_def_property_ui_text(prop, "Show Diffuse Color",
	                         "Show diffuse color of object and overlay sculpt mask on top of it");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_ShowDiffuseColor_update");

	prop = RNA_def_property(srna, "detail_size", PROP_INT, PROP_DISTANCE);
	RNA_def_property_ui_range(prop, 2, 100, 0, 0);
	RNA_def_property_ui_text(prop, "Detail Size", "Maximum edge length for dynamic topology sculpting (in pixels)");

	prop = RNA_def_property(srna, "use_smooth_shading", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DYNTOPO_SMOOTH_SHADING);
	RNA_def_property_ui_text(prop, "Smooth Shading",
	                         "Show faces in dynamic-topology mode with smooth "
	                         "shading rather than flat shaded");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_update");

	prop = RNA_def_property(srna, "use_edge_collapse", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DYNTOPO_COLLAPSE);
	RNA_def_property_ui_text(prop, "Collapse Short Edges",
	                         "In dynamic-topology mode, collapse short edges "
	                         "in addition to subdividing long ones");

	prop = RNA_def_property(srna, "symmetrize_direction", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, symmetrize_direction_items);
	RNA_def_property_ui_text(prop, "Direction", "Source and destination for symmetrize operator");
}


static void rna_def_uv_sculpt(BlenderRNA  *brna)
{
	StructRNA *srna;

	srna = RNA_def_struct(brna, "UvSculpt", "Paint");
	RNA_def_struct_path_func(srna, "rna_UvSculpt_path");
	RNA_def_struct_ui_text(srna, "UV Sculpting", "");
}


/* use for weight paint too */
static void rna_def_vertex_paint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "VertexPaint", "Paint");
	RNA_def_struct_sdna(srna, "VPaint");
	RNA_def_struct_path_func(srna, "rna_VertexPaint_path");
	RNA_def_struct_ui_text(srna, "Vertex Paint", "Properties of vertex and weight paint mode");

	/* vertex paint only */
	prop = RNA_def_property(srna, "use_all_faces", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_AREA);
	RNA_def_property_ui_text(prop, "All Faces", "Paint on all faces inside brush");

	prop = RNA_def_property(srna, "use_normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_NORMALS);
	RNA_def_property_ui_text(prop, "Normals", "Apply the vertex normal before painting");
	
	prop = RNA_def_property(srna, "use_spray", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_SPRAY);
	RNA_def_property_ui_text(prop, "Spray", "Keep applying paint effect while holding mouse");

	/* weight paint only */
	prop = RNA_def_property(srna, "use_group_restrict", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_ONLYVGROUP);
	RNA_def_property_ui_text(prop, "Restrict", "Restrict painting to verts already apart of the vertex group");
}

static void rna_def_image_paint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna = RNA_def_struct(brna, "ImagePaint", "Paint");
	RNA_def_struct_sdna(srna, "ImagePaintSettings");
	RNA_def_struct_path_func(srna, "rna_ImagePaintSettings_path");
	RNA_def_struct_ui_text(srna, "Image Paint", "Properties of image and texture painting mode");
	
	/* booleans */
	prop = RNA_def_property(srna, "use_projection", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_DISABLE);
	RNA_def_property_ui_text(prop, "Project Paint",
	                         "Use projection painting for improved consistency in the brush strokes");
	
	prop = RNA_def_property(srna, "use_occlude", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_XRAY);
	RNA_def_property_ui_text(prop, "Occlude", "Only paint onto the faces directly under the brush (slower)");
	
	prop = RNA_def_property(srna, "use_backface_culling", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_BACKFACE);
	RNA_def_property_ui_text(prop, "Cull", "Ignore faces pointing away from the view (faster)");
	
	prop = RNA_def_property(srna, "use_normal_falloff", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_FLAT);
	RNA_def_property_ui_text(prop, "Normal", "Paint most on faces pointing towards the view");
	
	prop = RNA_def_property(srna, "use_stencil_layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_STENCIL);
	RNA_def_property_ui_text(prop, "Stencil Layer", "Set the mask layer from the UV map buttons");
	
	prop = RNA_def_property(srna, "invert_stencil", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_STENCIL_INV);
	RNA_def_property_ui_text(prop, "Invert", "Invert the stencil layer");
	
	prop = RNA_def_property(srna, "use_clone_layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_CLONE);
	RNA_def_property_ui_text(prop, "Clone Map",
	                         "Use another UV map as clone source, otherwise use the 3D cursor as the source");
	
	/* integers */
	
	prop = RNA_def_property(srna, "seam_bleed", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_ui_range(prop, 0, 8, 0, 0);
	RNA_def_property_ui_text(prop, "Bleed", "Extend paint beyond the faces UVs to reduce seams (in pixels, slower)");

	prop = RNA_def_property(srna, "normal_angle", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_range(prop, 0, 90);
	RNA_def_property_ui_text(prop, "Angle", "Paint most on faces pointing towards the view according to this angle");

	prop = RNA_def_int_array(srna, "screen_grab_size", 2, NULL, 0, 0, "screen_grab_size",
	                         "Size to capture the image for re-projecting", 0, 0);
	RNA_def_property_range(prop, 512, 16384);
}

static void rna_def_particle_edit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem select_mode_items[] = {
		{SCE_SELECT_PATH, "PATH", ICON_PARTICLE_PATH, "Path", "Path edit mode"},
		{SCE_SELECT_POINT, "POINT", ICON_PARTICLE_POINT, "Point", "Point select mode"},
		{SCE_SELECT_END, "TIP", ICON_PARTICLE_TIP, "Tip", "Tip select mode"},
		{0, NULL, 0, NULL, NULL}
	};

	static EnumPropertyItem puff_mode[] = {
		{0, "ADD", 0, "Add", "Make hairs more puffy"},
		{1, "SUB", 0, "Sub", "Make hairs less puffy"},
		{0, NULL, 0, NULL, NULL}
	};

	static EnumPropertyItem length_mode[] = {
		{0, "GROW", 0, "Grow", "Make hairs longer"},
		{1, "SHRINK", 0, "Shrink", "Make hairs shorter"},
		{0, NULL, 0, NULL, NULL}
	};

	static EnumPropertyItem edit_type_items[] = {
		{PE_TYPE_PARTICLES, "PARTICLES", 0, "Particles", ""},
		{PE_TYPE_SOFTBODY, "SOFT_BODY", 0, "Soft body", ""},
		{PE_TYPE_CLOTH, "CLOTH", 0, "Cloth", ""},
		{0, NULL, 0, NULL, NULL}
	};


	/* edit */

	srna = RNA_def_struct(brna, "ParticleEdit", NULL);
	RNA_def_struct_sdna(srna, "ParticleEditSettings");
	RNA_def_struct_path_func(srna, "rna_ParticleEdit_path");
	RNA_def_struct_ui_text(srna, "Particle Edit", "Properties of particle editing mode");

	prop = RNA_def_property(srna, "tool", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "brushtype");
	RNA_def_property_enum_items(prop, particle_edit_hair_brush_items);
	RNA_def_property_enum_funcs(prop, NULL, "rna_ParticleEdit_tool_set", "rna_ParticleEdit_tool_itemf");
	RNA_def_property_ui_text(prop, "Tool", "");

	prop = RNA_def_property(srna, "select_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "selectmode");
	RNA_def_property_enum_items(prop, select_mode_items);
	RNA_def_property_ui_text(prop, "Selection Mode", "Particle select and display mode");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_update");

	prop = RNA_def_property(srna, "use_preserve_length", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_KEEP_LENGTHS);
	RNA_def_property_ui_text(prop, "Keep Lengths", "Keep path lengths constant");

	prop = RNA_def_property(srna, "use_preserve_root", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_LOCK_FIRST);
	RNA_def_property_ui_text(prop, "Keep Root", "Keep root keys unmodified");

	prop = RNA_def_property(srna, "use_emitter_deflect", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_DEFLECT_EMITTER);
	RNA_def_property_ui_text(prop, "Deflect Emitter", "Keep paths from intersecting the emitter");

	prop = RNA_def_property(srna, "emitter_distance", PROP_FLOAT, PROP_UNSIGNED);
	RNA_def_property_float_sdna(prop, NULL, "emitterdist");
	RNA_def_property_ui_range(prop, 0.0f, 10.0f, 10, 3);
	RNA_def_property_ui_text(prop, "Emitter Distance", "Distance to keep particles away from the emitter");

	prop = RNA_def_property(srna, "use_fade_time", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_FADE_TIME);
	RNA_def_property_ui_text(prop, "Fade Time", "Fade paths and keys further away from current frame");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_update");

	prop = RNA_def_property(srna, "use_auto_velocity", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_AUTO_VELOCITY);
	RNA_def_property_ui_text(prop, "Auto Velocity", "Calculate point velocities automatically");

	prop = RNA_def_property(srna, "show_particles", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_DRAW_PART);
	RNA_def_property_ui_text(prop, "Draw Particles", "Draw actual particles");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

	prop = RNA_def_property(srna, "use_default_interpolate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_INTERPOLATE_ADDED);
	RNA_def_property_ui_text(prop, "Interpolate", "Interpolate new particles from the existing ones");

	prop = RNA_def_property(srna, "default_key_count", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "totaddkey");
	RNA_def_property_range(prop, 2, SHRT_MAX);
	RNA_def_property_ui_range(prop, 2, 20, 10, 3);
	RNA_def_property_ui_text(prop, "Keys", "How many keys to make new particles with");

	prop = RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ParticleBrush");
	RNA_def_property_pointer_funcs(prop, "rna_ParticleEdit_brush_get", NULL, NULL, NULL);
	RNA_def_property_ui_text(prop, "Brush", "");

	prop = RNA_def_property(srna, "draw_step", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_text(prop, "Steps", "How many steps to draw the path with");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

	prop = RNA_def_property(srna, "fade_frames", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 100);
	RNA_def_property_ui_text(prop, "Frames", "How many frames to fade");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_update");

	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "edittype");
	RNA_def_property_enum_items(prop, edit_type_items);
	RNA_def_property_ui_text(prop, "Type", "");
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

	prop = RNA_def_property(srna, "is_editable", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_ParticleEdit_editable_get", NULL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Editable", "A valid edit mode exists");

	prop = RNA_def_property(srna, "is_hair", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_ParticleEdit_hair_get", NULL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Hair", "Editing hair");

	prop = RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Object", "The edited object");


	/* brush */

	srna = RNA_def_struct(brna, "ParticleBrush", NULL);
	RNA_def_struct_sdna(srna, "ParticleBrushData");
	RNA_def_struct_ui_text(srna, "Particle Brush", "Particle editing brush");

	prop = RNA_def_property(srna, "size", PROP_INT, PROP_DISTANCE);
	RNA_def_property_range(prop, 1, SHRT_MAX);
	RNA_def_property_ui_range(prop, 1, 100, 10, 3);
	RNA_def_property_ui_text(prop, "Radius", "Radius of the brush in pixels");

	prop = RNA_def_property(srna, "strength", PROP_FLOAT, PROP_FACTOR);
	RNA_def_property_range(prop, 0.001, 1.0);
	RNA_def_property_ui_text(prop, "Strength", "Brush strength");

	prop = RNA_def_property(srna, "count", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 1000);
	RNA_def_property_ui_range(prop, 1, 100, 10, 3);
	RNA_def_property_ui_text(prop, "Count", "Particle count");

	prop = RNA_def_property(srna, "steps", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "step");
	RNA_def_property_range(prop, 1, SHRT_MAX);
	RNA_def_property_ui_range(prop, 1, 50, 10, 3);
	RNA_def_property_ui_text(prop, "Steps", "Brush steps");

	prop = RNA_def_property(srna, "puff_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "invert");
	RNA_def_property_enum_items(prop, puff_mode);
	RNA_def_property_ui_text(prop, "Puff Mode", "");

	prop = RNA_def_property(srna, "use_puff_volume", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_BRUSH_DATA_PUFF_VOLUME);
	RNA_def_property_ui_text(prop, "Puff Volume",
	                         "Apply puff to unselected end-points (helps maintain hair volume when puffing root)");

	prop = RNA_def_property(srna, "length_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "invert");
	RNA_def_property_enum_items(prop, length_mode);
	RNA_def_property_ui_text(prop, "Length Mode", "");

	/* dummy */
	prop = RNA_def_property(srna, "curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "CurveMapping");
	RNA_def_property_pointer_funcs(prop, "rna_ParticleBrush_curve_get", NULL, NULL, NULL);
	RNA_def_property_ui_text(prop, "Curve", "");
}

void RNA_def_sculpt_paint(BlenderRNA *brna)
{
	rna_def_paint(brna);
	rna_def_sculpt(brna);
	rna_def_uv_sculpt(brna);
	rna_def_vertex_paint(brna);
	rna_def_image_paint(brna);
	rna_def_particle_edit(brna);
}

#endif
