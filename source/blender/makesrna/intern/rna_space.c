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
 * Contributor(s): Blender Foundation (2008)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_action_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_view3d_types.h"

#include "WM_types.h"

EnumPropertyItem space_type_items[] = {
	{SPACE_EMPTY, "EMPTY", 0, "Empty", ""},
	{SPACE_VIEW3D, "VIEW_3D", 0, "3D View", ""},
	{SPACE_IPO, "GRAPH_EDITOR", 0, "Graph Editor", ""},
	{SPACE_OUTLINER, "OUTLINER", 0, "Outliner", ""},
	{SPACE_BUTS, "BUTTONS_WINDOW", 0, "Buttons Window", ""},
	{SPACE_FILE, "FILE_BROWSER", 0, "File Browser", ""},
	{SPACE_IMAGE, "IMAGE_EDITOR", 0, "Image Editor", ""},
	{SPACE_INFO, "USER_PREFERENCES", 0, "User Preferences", ""},
	{SPACE_SEQ, "SEQUENCE_EDITOR", 0, "Sequence Editor", ""},
	{SPACE_TEXT, "TEXT_EDITOR", 0, "Text Editor", ""},
	//{SPACE_IMASEL, "IMAGE_BROWSER", 0, "Image Browser", ""},
	{SPACE_SOUND, "AUDIO_WINDOW", 0, "Audio Window", ""},
	{SPACE_ACTION, "DOPESHEET_EDITOR", 0, "DopeSheet Editor", ""},
	{SPACE_NLA, "NLA_EDITOR", 0, "NLA Editor", ""},
	{SPACE_SCRIPT, "SCRIPTS_WINDOW", 0, "Scripts Window", ""},
	{SPACE_TIME, "TIMELINE", 0, "Timeline", ""},
	{SPACE_NODE, "NODE_EDITOR", 0, "Node Editor", ""},
	{SPACE_LOGIC, "LOGIC_EDITOR", 0, "Logic Editor", ""},
	{SPACE_CONSOLE, "CONSOLE", 0, "Console", ""},
	{0, NULL, 0, NULL, NULL}};

#define DC_RGB {0, "COLOR", ICON_IMAGE_RGB, "Color", "Draw image with RGB colors."}
#define DC_RGBA {SI_USE_ALPHA, "COLOR_ALPHA", ICON_IMAGE_RGB_ALPHA, "Color and Alpha", "Draw image with RGB colors and alpha transparency."}
#define DC_ALPHA {SI_SHOW_ALPHA, "ALPHA", ICON_IMAGE_ALPHA, "Alpha", "Draw alpha transparency channel."}
#define DC_Z {SI_SHOW_ZBUF, "Z_BUFFER", ICON_IMAGE_ZDEPTH, "Z-Buffer", "Draw Z-buffer associated with image (mapped from camera clip start to end)."}
#ifdef WITH_LCMS
#define DC_LCMS {SI_COLOR_CORRECTION, "COLOR_CORRECTED", ICON_IMAGE_ALPHA, "Color Corrected", "Display color corrected image."}
#else
#define DC_LCMS {0, NULL, 0, NULL, NULL}
#endif
#define DC_ZERO {0, NULL, 0, NULL, NULL}

static EnumPropertyItem dc_all_items[] = {DC_RGB, DC_RGBA, DC_ALPHA, DC_Z, DC_LCMS, DC_ZERO};

#ifdef RNA_RUNTIME

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"

#include "BKE_brush.h"
#include "BKE_context.h"

#include "ED_image.h"

#include "IMB_imbuf_types.h"

static StructRNA* rna_Space_refine(struct PointerRNA *ptr)
{
	SpaceLink *space= (SpaceLink*)ptr->data;

	switch(space->spacetype) {
		case SPACE_VIEW3D:
			return &RNA_Space3DView;
		case SPACE_IPO:
			return &RNA_SpaceGraphEditor;
		case SPACE_OUTLINER:
			return &RNA_SpaceOutliner;
		case SPACE_BUTS:
			return &RNA_SpaceButtonsWindow;
		case SPACE_FILE:
			return &RNA_SpaceFileBrowser;
		case SPACE_IMAGE:
			return &RNA_SpaceImageEditor;
		/*case SPACE_INFO:
			return &RNA_SpaceUserPreferences;*/
		case SPACE_SEQ:
			return &RNA_SpaceSequenceEditor;
		case SPACE_TEXT:
			return &RNA_SpaceTextEditor;
		//case SPACE_IMASEL:
		//	return &RNA_SpaceImageBrowser;
		/*case SPACE_SOUND:
			return &RNA_SpaceAudioWindow;*/
		case SPACE_ACTION:
			return &RNA_SpaceDopeSheetEditor;
		case SPACE_NLA:
			return &RNA_SpaceNLA;
		/*case SPACE_SCRIPT:
			return &RNA_SpaceScriptsWindow;
		case SPACE_TIME:
			return &RNA_SpaceTimeline;
		case SPACE_NODE:
			return &RNA_SpaceNodeEditor;
		case SPACE_LOGIC:
			return &RNA_SpaceLogicEditor;*/
		case SPACE_CONSOLE:
			return &RNA_SpaceConsole;
		default:
			return &RNA_Space;
	}
}

/* Space Image Editor */

static PointerRNA rna_SpaceImageEditor_uvedit_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_SpaceUVEditor, ptr->data);
}

static void rna_SpaceImageEditor_paint_update(bContext *C, PointerRNA *ptr)
{
	Scene *scene= CTX_data_scene(C);

	if(scene)
		brush_check_exists(&scene->toolsettings->imapaint.brush);
}

static int rna_SpaceImageEditor_show_render_get(PointerRNA *ptr)
{
	SpaceImage *sima= (SpaceImage*)(ptr->data);
	return ED_space_image_show_render(sima);
}

static int rna_SpaceImageEditor_show_paint_get(PointerRNA *ptr)
{
	SpaceImage *sima= (SpaceImage*)(ptr->data);
	return ED_space_image_show_paint(sima);
}

static int rna_SpaceImageEditor_show_uvedit_get(PointerRNA *ptr)
{
	SpaceImage *sima= (SpaceImage*)(ptr->data);
	bScreen *sc= (bScreen*)ptr->id.data;
	return ED_space_image_show_uvedit(sima, sc->scene->obedit);
}

static void rna_SpaceImageEditor_image_set(PointerRNA *ptr, PointerRNA value)
{
	SpaceImage *sima= (SpaceImage*)(ptr->data);
	bScreen *sc= (bScreen*)ptr->id.data;

	ED_space_image_set(NULL, sima, sc->scene, sc->scene->obedit, (Image*)value.data);
}

static EnumPropertyItem dc_rgb_items[] = {DC_RGB, DC_LCMS, DC_ZERO};
static EnumPropertyItem dc_alpha_items[] = {DC_RGB, DC_RGBA, DC_ALPHA, DC_LCMS, DC_ZERO};
static EnumPropertyItem dc_z_items[] = {DC_RGB, DC_Z, DC_LCMS, DC_ZERO};

static EnumPropertyItem *rna_SpaceImageEditor_draw_channels_itemf(bContext *C, PointerRNA *ptr, int *free)
{
	SpaceImage *sima= (SpaceImage*)ptr->data;
	ImBuf *ibuf= ED_space_image_buffer(sima);
	int zbuf, alpha;

	if(C==NULL) {
		/* needed for doc generation */
		return dc_all_items;
	}
	
	alpha= ibuf && (ibuf->channels == 4);
	zbuf= ibuf && (ibuf->zbuf || ibuf->zbuf_float || (ibuf->channels==1));

	if(alpha && zbuf)
		return dc_all_items;
	else if(alpha)
		return dc_alpha_items;
	else if(zbuf)
		return dc_z_items;
	else
		return dc_rgb_items;
}

/* Space Text Editor */

void rna_SpaceTextEditor_word_wrap_set(PointerRNA *ptr, int value)
{
	SpaceText *st= (SpaceText*)(ptr->data);

	st->wordwrap= value;
	st->left= 0;
}

void rna_SpaceTextEditor_text_set(PointerRNA *ptr, PointerRNA value)
{
	SpaceText *st= (SpaceText*)(ptr->data);

	st->text= value.data;
	st->top= 0;
}

void rna_SpaceFileBrowser_params_set(PointerRNA *ptr, PointerRNA value)
{
	SpaceFile *sfile= (SpaceFile*)(ptr->data);

	sfile->params= value.data;
}

/* Space Buttons */

StructRNA *rna_SpaceButtonsWindow_pin_id_typef(PointerRNA *ptr)
{
	SpaceButs *sbuts= (SpaceButs*)(ptr->data);

	if(sbuts->pinid)
		return ID_code_to_RNA_type(GS(sbuts->pinid->name));

	return &RNA_ID;
}

void rna_SpaceButtonsWindow_align_set(PointerRNA *ptr, int value)
{
	SpaceButs *sbuts= (SpaceButs*)(ptr->data);

	sbuts->align= value;
	sbuts->re_align= 1;
}

/* Space Console */
static void rna_ConsoleLine_line_get(PointerRNA *ptr, char *value)
{
	ConsoleLine *ci= (ConsoleLine*)ptr->data;
	strcpy(value, ci->line);
}

static int rna_ConsoleLine_line_length(PointerRNA *ptr)
{
	ConsoleLine *ci= (ConsoleLine*)ptr->data;
	return ci->len;
}

static void rna_ConsoleLine_line_set(PointerRNA *ptr, const char *value)
{
	ConsoleLine *ci= (ConsoleLine*)ptr->data;
	int len= strlen(value);
	
	if(len < ci->len_alloc) { /* allocated size is enough? */
		strcpy(ci->line, value);
	}
	else { /* allocate a new strnig */
		MEM_freeN(ci->line);
		ci->line= BLI_strdup(value);
		ci->len_alloc= len;
	}
	ci->len= len;

	if(ci->cursor > len) /* clamp the cursor */
		ci->cursor= len;
}

static void rna_ConsoleLine_cursor_index_range(PointerRNA *ptr, int *min, int *max)
{
	ConsoleLine *ci= (ConsoleLine*)ptr->data;

	*min= 0;
	*max= ci->len;
}

#else

static void rna_def_space(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "Space", NULL);
	RNA_def_struct_sdna(srna, "SpaceLink");
	RNA_def_struct_ui_text(srna, "Space", "Space data for a screen area.");
	RNA_def_struct_refine_func(srna, "rna_Space_refine");
	
	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "spacetype");
	RNA_def_property_enum_items(prop, space_type_items);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Type", "Space data type.");
}

static void rna_def_space_image_uv(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem sticky_mode_items[] = {
		{SI_STICKY_DISABLE, "DISABLED", ICON_STICKY_UVS_DISABLE, "Disabled", "Sticky vertex selection disabled."},
		{SI_STICKY_LOC, "SHARED_LOCATION", ICON_STICKY_UVS_LOC, "Shared Location", "Select UVs that are at the same location and share a mesh vertex."},
		{SI_STICKY_VERTEX, "SHARED_VERTEX", ICON_STICKY_UVS_VERT, "Shared Vertex", "Select UVs that share mesh vertex, irrespective if they are in the same location."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem dt_uv_items[] = {
		{SI_UVDT_OUTLINE, "OUTLINE", 0, "Outline", "Draw white edges with black outline."},
		{SI_UVDT_DASH, "DASH", 0, "Dash", "Draw dashed black-white edges."},
		{SI_UVDT_BLACK, "BLACK", 0, "Black", "Draw black edges."},
		{SI_UVDT_WHITE, "WHITE", 0, "White", "Draw white edges."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem dt_uvstretch_items[] = {
		{SI_UVDT_STRETCH_ANGLE, "ANGLE", 0, "Angle", "Angular distortion between UV and 3D angles."},
		{SI_UVDT_STRETCH_AREA, "AREA", 0, "Area", "Area distortion between UV and 3D faces."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem pivot_items[] = {
		{V3D_CENTER, "CENTER", ICON_ROTATE, "Bounding Box Center", ""},
		{V3D_CENTROID, "MEDIAN", ICON_ROTATECENTER, "Median Point", ""},
		{V3D_CURSOR, "CURSOR", ICON_CURSOR, "2D Cursor", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "SpaceUVEditor", NULL);
	RNA_def_struct_sdna(srna, "SpaceImage");
	RNA_def_struct_nested(brna, srna, "SpaceImageEditor");
	RNA_def_struct_ui_text(srna, "Space UV Editor", "UV editor data for the image editor space.");

	/* selection */
	prop= RNA_def_property(srna, "sticky_selection_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "sticky");
	RNA_def_property_enum_items(prop, sticky_mode_items);
	RNA_def_property_ui_text(prop, "Sticky Selection Mode", "Automatically select also UVs sharing the same vertex as the ones being selected.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	/* drawing */
	prop= RNA_def_property(srna, "edge_draw_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "dt_uv");
	RNA_def_property_enum_items(prop, dt_uv_items);
	RNA_def_property_ui_text(prop, "Edge Draw Type", "Draw type for drawing UV edges.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "draw_smooth_edges", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_SMOOTH_UV);
	RNA_def_property_ui_text(prop, "Draw Smooth Edges", "Draw UV edges anti-aliased.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "draw_stretch", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAW_STRETCH);
	RNA_def_property_ui_text(prop, "Draw Stretch", "Draw faces colored according to the difference in shape between UVs and their 3D coordinates (blue for low distortion, red for high distortion).");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "draw_stretch_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "dt_uvstretch");
	RNA_def_property_enum_items(prop, dt_uvstretch_items);
	RNA_def_property_ui_text(prop, "Draw Stretch Type", "Type of stretch to draw.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "draw_modified_edges", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAWSHADOW);
	RNA_def_property_ui_text(prop, "Draw Modified Edges", "Draw edges after modifiers are applied.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "draw_other_objects", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAW_OTHER);
	RNA_def_property_ui_text(prop, "Draw Other Objects", "Draw other selected objects that share the same image.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "normalized_coordinates", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_COORDFLOATS);
	RNA_def_property_ui_text(prop, "Normalized Coordinates", "Display UV coordinates from 0.0 to 1.0 rather than in pixels.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	/* todo: move edge and face drawing options here from G.f */

	prop= RNA_def_property(srna, "snap_to_pixels", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_PIXELSNAP);
	RNA_def_property_ui_text(prop, "Snap to Pixels", "Snap UVs to pixel locations while editing.");

	prop= RNA_def_property(srna, "constrain_to_image_bounds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_CLIP_UV);
	RNA_def_property_ui_text(prop, "Constrain to Image Bounds", "Constraint to stay within the image bounds while editing.");

	prop= RNA_def_property(srna, "live_unwrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_LIVE_UNWRAP);
	RNA_def_property_ui_text(prop, "Live Unwrap", "Continuously unwrap the selected UV island while transforming pinned vertices.");

	prop= RNA_def_property(srna, "pivot", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "around");
	RNA_def_property_enum_items(prop, pivot_items);
	RNA_def_property_ui_text(prop, "Pivot", "Rotation/Scaling Pivot.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);
}

static void rna_def_space_outliner(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem display_mode_items[] = {
		{0, "ALL_SCENES", 0, "All Scenes", ""},
		{1, "CURRENT_SCENE", 0, "Current Scene", ""},
		{2, "VISIBLE_LAYERS", 0, "Visible Layers", ""},
		{3, "SELECTED", 0, "Selected", ""},
		{4, "ACTIVE", 0, "Active", ""},
		{5, "SAME_TYPES", 0, "Same Types", ""},
		{6, "GROUPS", 0, "Groups", ""},
		{7, "LIBRARIES", 0, "Libraries", ""},
		{10, "SEQUENCE", 0, "Sequence", ""},
		{11, "DATABLOCKS", 0, "Datablocks", ""},
		{12, "USER_PREFERENCES", 0, "User Preferences", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "SpaceOutliner", "Space");
	RNA_def_struct_sdna(srna, "SpaceOops");
	RNA_def_struct_ui_text(srna, "Space Outliner", "Outliner space data.");
	
	prop= RNA_def_property(srna, "display_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "outlinevis");
	RNA_def_property_enum_items(prop, display_mode_items);
	RNA_def_property_ui_text(prop, "Display Mode", "Type of information to display");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "show_restriction_columns", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SO_HIDE_RESTRICTCOLS);
	RNA_def_property_ui_text(prop, "Show Restriction Columns", "Show colum");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

}

static void rna_def_background_image(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "BackgroundImage", NULL);
	RNA_def_struct_sdna(srna, "BGpic");
	RNA_def_struct_ui_text(srna, "Background Image", "Image and settings for display in the 3d View background.");

	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ima");
	RNA_def_property_ui_text(prop, "Image", "Image displayed and edited in this space.");
	RNA_def_property_update(prop, NC_OBJECT|ND_GEOM_DATA, NULL);

	prop= RNA_def_property(srna, "image_user", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "iuser");
	RNA_def_property_ui_text(prop, "Image User", "Parameters defining which layer, pass and frame of the image is displayed.");
	
	prop= RNA_def_property(srna, "x_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xof");
	RNA_def_property_ui_text(prop, "X Offset", "Offsets image horizontally from the view center");
	
	prop= RNA_def_property(srna, "y_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "yof");
	RNA_def_property_ui_text(prop, "Y Offset", "Offsets image vertically from the view center");
	
	prop= RNA_def_property(srna, "size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Size", "Scaling factor for the background image.");
	RNA_def_property_range(prop, 0.0, FLT_MAX);
	
	prop= RNA_def_property(srna, "transparency", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "blend");
	RNA_def_property_ui_text(prop, "Transparency", "Amount to blend the image against the background color.");
	RNA_def_property_range(prop, 0.0, 1.0);

}

static void rna_def_space_3dview(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem viewport_shading_items[] = {
		{OB_BOUNDBOX, "BOUNDBOX", 0, "Bounding Box", "Display the object's local bounding boxes only"},
		{OB_WIRE, "WIREFRAME", 0, "Wireframe", "Display the object as wire edges"},
		{OB_SOLID, "SOLID", 0, "Solid", "Display the object solid, lit with default OpenGL lights"},
		{OB_SHADED, "SHADED", 0, "Shaded", "Display the object solid, with preview shading interpolated at vertices"},
		{OB_TEXTURE, "TEXTURED", 0, "Textured", "Display the object solid, with face-assigned textures"},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem pivot_items[] = {
		{V3D_CENTER, "BOUNDING_BOX_CENTER", 0, "Bounding Box Center", ""},
		{V3D_CURSOR, "CURSOR", 0, "3D Cursor", ""},
		{V3D_LOCAL, "INDIVIDUAL_CENTERS", 0, "Individual Centers", ""},
		{V3D_CENTROID, "MEDIAN_POINT", 0, "Median Point", ""},
		{V3D_ACTIVE, "ACTIVE_ELEMENT", 0, "Active Element", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem transform_orientation_items[] = {
		{V3D_MANIP_GLOBAL, "ORIENT_GLOBAL", 0, "Global", "Align the transformation axes to world space"},
		{V3D_MANIP_LOCAL, "ORIENT_LOCAL", 0, "Local", "Align the transformation axes to the selected objects' local space"},
		{V3D_MANIP_NORMAL, "ORIENT_NORMAL", 0, "Normal", "Align the transformation axes to average normal of selected elements (bone Y axis for pose mode)"},
		{V3D_MANIP_VIEW, "ORIENT_VIEW", 0, "View", "Align the transformation axes to the window"},
		{V3D_MANIP_CUSTOM, "ORIENT_CUSTOM", 0, "Custom", "Use a custom transform orientation"},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "Space3DView", "Space");
	RNA_def_struct_sdna(srna, "View3D");
	RNA_def_struct_ui_text(srna, "3D View Space", "3D View space data");
	
	prop= RNA_def_property(srna, "camera", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "camera");
	RNA_def_property_ui_text(prop, "Camera", "Active camera used in this view (when unlocked from the scene's active camera).");
	
	prop= RNA_def_property(srna, "lock_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ob_centre");
	RNA_def_property_ui_text(prop, "Lock Object", "3D View center is locked to this object's position");
	
	prop= RNA_def_property(srna, "background_image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "bgpic");
	RNA_def_property_ui_text(prop, "Background Image", "Image and settings to display in the 3D View background");

	prop= RNA_def_property(srna, "viewport_shading", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "drawtype");
	RNA_def_property_enum_items(prop, viewport_shading_items);
	RNA_def_property_ui_text(prop, "Viewport Shading", "Method to display/shade objects in the 3D View.");

	prop= RNA_def_property(srna, "localview", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "localview", 0);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Local View", "Display an isolated sub-set of objects, apart from the scene visibility.");

	prop= RNA_def_property(srna, "lens", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "lens");
	RNA_def_property_ui_text(prop, "Lens", "Lens angle (mm) in perspective view.");
	RNA_def_property_range(prop, 1.0f, 250.0f);
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "clip_start", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "near");
	RNA_def_property_range(prop, 0.0f, FLT_MAX);
	RNA_def_property_ui_text(prop, "Clip Start", "3D View near clipping distance.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "clip_end", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "far");
	RNA_def_property_range(prop, 1.0f, FLT_MAX);
	RNA_def_property_ui_text(prop, "Clip End", "3D View far clipping distance.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "grid_spacing", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "grid");
	RNA_def_property_ui_text(prop, "Grid Spacing", "The distance between 3D View grid lines.");
	RNA_def_property_range(prop, 0.0f, FLT_MAX);
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "grid_lines", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gridlines");
	RNA_def_property_ui_text(prop, "Grid Lines", "The number of grid lines to display in perspective view.");
	RNA_def_property_range(prop, 0, 1024);
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "grid_subdivisions", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gridsubdiv");
	RNA_def_property_ui_text(prop, "Grid Subdivisions", "The number of subdivisions between grid lines.");
	RNA_def_property_range(prop, 1, 1024);
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "display_floor", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_FLOOR);
	RNA_def_property_ui_text(prop, "Display Grid Floor", "Show the ground plane grid in perspective view.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "display_x_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_X);
	RNA_def_property_ui_text(prop, "Display X Axis", "Show the X axis line in perspective view.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "display_y_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_Y);
	RNA_def_property_ui_text(prop, "Display Y Axis", "Show the Y axis line in perspective view.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "display_z_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_Z);
	RNA_def_property_ui_text(prop, "Display Z Axis", "Show the Z axis line in perspective view.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "outline_selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", V3D_SELECT_OUTLINE);
	RNA_def_property_ui_text(prop, "Outline Selected", "Show an outline highlight around selected objects in non-wireframe views.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "all_object_centers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", V3D_DRAW_CENTERS);
	RNA_def_property_ui_text(prop, "All Object Centers", "Show the object center dot for all (selected and unselected) objects.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "relationship_lines", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", V3D_HIDE_HELPLINES);
	RNA_def_property_ui_text(prop, "Relationship Lines", "Show dashed lines indicating parent or constraint relationships.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "textured_solid", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag2", V3D_SOLID_TEX);
	RNA_def_property_ui_text(prop, "Textured Solid", "Display face-assigned textures in solid view");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "display_background_image", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", V3D_DISPBGPIC);
	RNA_def_property_ui_text(prop, "Display Background Image", "Display a reference image behind objects in the 3D View");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "pivot_point", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "around");
	RNA_def_property_enum_items(prop, pivot_items);
	RNA_def_property_ui_text(prop, "Pivot Point", "Pivot center for rotation/scaling.");
	
	prop= RNA_def_property(srna, "manipulator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twflag", V3D_USE_MANIPULATOR);
	RNA_def_property_ui_text(prop, "Manipulator", "Use a 3D manipulator widget for controlling transforms.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, NULL);
	
	prop= RNA_def_property(srna, "manipulator_translate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twtype", V3D_MANIP_TRANSLATE);
	RNA_def_property_ui_text(prop, "Manipulator Translate", "Use the manipulator for movement transformations.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, NULL);
	
	prop= RNA_def_property(srna, "manipulator_rotate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twtype", V3D_MANIP_ROTATE);
	RNA_def_property_ui_text(prop, "Manipulator Rotate", "Use the manipulator for rotation transformations.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, NULL);
	
	prop= RNA_def_property(srna, "manipulator_scale", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twtype", V3D_MANIP_SCALE);
	RNA_def_property_ui_text(prop, "Manipulator Scale", "Use the manipulator for scale transformations.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, NULL);
	
	prop= RNA_def_property(srna, "transform_orientation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "twmode");
	RNA_def_property_enum_items(prop, transform_orientation_items);
	RNA_def_property_ui_text(prop, "Transform Orientation", "The alignment of manipulator handles.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, NULL);

	prop= RNA_def_property(srna, "lock_rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, "RegionView3D", "viewlock", RV3D_LOCKED);
	RNA_def_property_ui_text(prop, "Lock", "Lock View Rotation");
	
	prop= RNA_def_property(srna, "box_preview", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, "RegionView3D", "viewlock", RV3D_BOXVIEW);
	RNA_def_property_ui_text(prop, "Box", "");
	
	prop= RNA_def_property(srna, "box_clip", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, "RegionView3D", "viewlock", RV3D_BOXCLIP);
	RNA_def_property_ui_text(prop, "Clip", "");
}

static void rna_def_space_buttons(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem buttons_context_items[] = {
		{BCONTEXT_SCENE, "SCENE", ICON_SCENE, "Scene", "Scene"},
		{BCONTEXT_WORLD, "WORLD", ICON_WORLD, "World", "World"},
		{BCONTEXT_OBJECT, "OBJECT", ICON_OBJECT_DATA, "Object", "Object"},
		{BCONTEXT_CONSTRAINT, "CONSTRAINT", ICON_CONSTRAINT, "Constraint", "Constraint"},
		{BCONTEXT_MODIFIER, "MODIFIER", ICON_MODIFIER, "Modifier", "Modifier"},
		{BCONTEXT_DATA, "DATA", 0, "Data", "Data"},
		{BCONTEXT_BONE, "BONE", ICON_BONE_DATA, "Bone", "Bone"},
		{BCONTEXT_MATERIAL, "MATERIAL", ICON_MATERIAL, "Material", "Material"},
		{BCONTEXT_TEXTURE, "TEXTURE", ICON_TEXTURE, "Texture", "Texture"},
		{BCONTEXT_PARTICLE, "PARTICLE", ICON_PARTICLES, "Particle", "Particle"},
		{BCONTEXT_PHYSICS, "PHYSICS", ICON_PHYSICS, "Physics", "Physics"},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem align_items[] = {
		{BUT_HORIZONTAL, "HORIZONTAL", 0, "Horizontal", ""},
		{BUT_VERTICAL, "VERTICAL", 0, "Vertical", ""},
		{0, NULL, 0, NULL, NULL}};
		
	srna= RNA_def_struct(brna, "SpaceButtonsWindow", "Space");
	RNA_def_struct_sdna(srna, "SpaceButs");
	RNA_def_struct_ui_text(srna, "Buttons Space", "Buttons Window space data");
	
	prop= RNA_def_property(srna, "context", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mainb");
	RNA_def_property_enum_items(prop, buttons_context_items);
	RNA_def_property_ui_text(prop, "Context", "Type of active data to display and edit.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "align", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "align");
	RNA_def_property_enum_items(prop, align_items);
	RNA_def_property_enum_funcs(prop, NULL, "rna_SpaceButtonsWindow_align_set", NULL);
	RNA_def_property_ui_text(prop, "Align", "Arrangement of the panels.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	/* pinned data */
	prop= RNA_def_property(srna, "pin_id", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pinid");
	RNA_def_property_struct_type(prop, "ID");
	RNA_def_property_pointer_funcs(prop, NULL, NULL, "rna_SpaceButtonsWindow_pin_id_typef");
	RNA_def_property_flag(prop, PROP_EDITABLE);
}

static void rna_def_space_image(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "SpaceImageEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceImage");
	RNA_def_struct_ui_text(srna, "Space Image Editor", "Image and UV editor space data.");

	/* image */
	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_funcs(prop, NULL, "rna_SpaceImageEditor_image_set", NULL);
	RNA_def_property_ui_text(prop, "Image", "Image displayed and edited in this space.");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "image_user", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "iuser");
	RNA_def_property_ui_text(prop, "Image User", "Parameters defining which layer, pass and frame of the image is displayed.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "curves", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "cumap");
	RNA_def_property_ui_text(prop, "Curves", "Color curve mapping to use for displaying the image.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "image_pin", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "pin", 0);
	RNA_def_property_ui_text(prop, "Image Pin", "Display current image regardless of object selection.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	/* image draw */
	prop= RNA_def_property(srna, "draw_repeated", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAW_TILE);
	RNA_def_property_ui_text(prop, "Draw Repeated", "Draw the image repeated outside of the main view.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "draw_channels", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "flag");
	RNA_def_property_enum_items(prop, dc_all_items);
	RNA_def_property_enum_funcs(prop, NULL, NULL, "rna_SpaceImageEditor_draw_channels_itemf");
	RNA_def_property_ui_text(prop, "Draw Channels", "Channels of the image to draw.");
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, NULL);

	/* uv */
	prop= RNA_def_property(srna, "uv_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "SpaceUVEditor");
	RNA_def_property_pointer_funcs(prop, "rna_SpaceImageEditor_uvedit_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "UV Editor", "UV editor settings.");
	
	/* paint */
	prop= RNA_def_property(srna, "image_painting", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAWTOOL);
	RNA_def_property_ui_text(prop, "Image Painting", "Enable image painting mode.");
	RNA_def_property_ui_icon(prop, ICON_TPAINT_HLT, 0);
	RNA_def_property_update(prop, NC_IMAGE|ND_DISPLAY, "rna_SpaceImageEditor_paint_update");

	/* grease pencil */
	prop= RNA_def_property(srna, "grease_pencil", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "gpd");
	RNA_def_property_struct_type(prop, "UnknownType");
	RNA_def_property_ui_text(prop, "Grease Pencil", "Grease pencil data for this space.");

	prop= RNA_def_property(srna, "use_grease_pencil", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DISPGP);
	RNA_def_property_ui_text(prop, "Use Grease Pencil", "Display and edit the grease pencil freehand annotations overlay.");

	/* update */
	prop= RNA_def_property(srna, "update_automatically", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "lock", 0);
	RNA_def_property_ui_icon(prop, ICON_UNLOCKED, 1);
	RNA_def_property_ui_text(prop, "Update Automatically", "Update other affected window spaces automatically to reflect changes during interactive operations such as transform.");

	/* state */
	prop= RNA_def_property(srna, "show_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_SpaceImageEditor_show_render_get", NULL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Show Render", "Show render related properties.");

	prop= RNA_def_property(srna, "show_paint", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_SpaceImageEditor_show_paint_get", NULL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Show Paint", "Show paint related properties.");

	prop= RNA_def_property(srna, "show_uvedit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_SpaceImageEditor_show_uvedit_get", NULL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Show UV Editor", "Show uv editing related properties.");

	rna_def_space_image_uv(brna);
}

static void rna_def_space_sequencer(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem display_mode_items[] = {
		{SEQ_DRAW_SEQUENCE, "SEQUENCER", 0, "Sequencer", ""},
		{SEQ_DRAW_IMG_IMBUF, "IMAGE", 0, "Image Preview", ""},
		{SEQ_DRAW_IMG_WAVEFORM, "WAVEFORM", 0, "Luma Waveform", ""},
		{SEQ_DRAW_IMG_VECTORSCOPE, "VECTOR_SCOPE", 0, "Chroma Vectorscope", ""},
		{SEQ_DRAW_IMG_HISTOGRAM, "HISTOGRAM", 0, "Histogram", ""},
		{0, NULL, 0, NULL, NULL}};
	
	srna= RNA_def_struct(brna, "SpaceSequenceEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceSeq");
	RNA_def_struct_ui_text(srna, "Space Sequence Editor", "Sequence editor space data.");
	
	/* display type, fairly important */
	prop= RNA_def_property(srna, "display_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mainb");
	RNA_def_property_enum_items(prop, display_mode_items);
	RNA_def_property_ui_text(prop, "Display Mode", "The view mode to use for displaying sequencer output.");
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);
		
	/* flag's */
	prop= RNA_def_property(srna, "draw_frames", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SEQ_DRAWFRAMES);
	RNA_def_property_ui_text(prop, "Draw Frames", "Draw frames rather then seconds.");
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "transform_markers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SEQ_MARKER_TRANS);
	RNA_def_property_ui_text(prop, "Transform Markers", "Transform markers as well as strips.");
	
	prop= RNA_def_property(srna, "seperate_color_preview", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SEQ_DRAW_COLOR_SEPERATED);
	RNA_def_property_ui_text(prop, "Seperate Colors", "Seperate color channels in preview.");
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "draw_safe_margin", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SEQ_DRAW_SAFE_MARGINS);
	RNA_def_property_ui_text(prop, "Safe Margin", "Draw title safe margins in preview.");	
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "use_grease_pencil", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SEQ_DRAW_GPENCIL);
	RNA_def_property_ui_text(prop, "Use Grease Pencil", "Display and edit the grease pencil freehand annotations overlay.");	
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);
	
	/* grease pencil */
	prop= RNA_def_property(srna, "grease_pencil", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "gpd");
	RNA_def_property_struct_type(prop, "UnknownType");
	RNA_def_property_ui_text(prop, "Grease Pencil", "Grease pencil data for this space.");
	
	prop= RNA_def_property(srna, "display_channel", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "chanshown");
	RNA_def_property_ui_text(prop, "Display Channel", "The channel number shown in the image preview. 0 is the result of all strips combined.");
	RNA_def_property_range(prop, 0, 32); // MAXSEQ --- todo, move from BKE_sequence.h
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "draw_overexposed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "zebra");
	RNA_def_property_ui_text(prop, "Show Overexposed", "Show overexposed areas with zebra stripes.");
	RNA_def_property_range(prop, 0, 110);
	RNA_def_property_update(prop, ND_SEQUENCER|NC_WINDOW, NULL);
	
	
	/* not sure we need rna access to these but adding anyway */
	prop= RNA_def_property(srna, "x_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xof");
	RNA_def_property_ui_text(prop, "X Offset", "Offsets image horizontally from the view center");

	prop= RNA_def_property(srna, "y_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "yof");
	RNA_def_property_ui_text(prop, "Y Offset", "Offsets image horizontally from the view center");
	
	prop= RNA_def_property(srna, "zoom", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zoom");
	RNA_def_property_ui_text(prop, "Zoom", "Display zoom level");	
}

static void rna_def_space_text(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "SpaceTextEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceText");
	RNA_def_struct_ui_text(srna, "Space Text Editor", "Text editor space data.");

	/* text */
	prop= RNA_def_property(srna, "text", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Text", "Text displayed and edited in this space.");
	RNA_def_property_pointer_funcs(prop, NULL, "rna_SpaceTextEditor_text_set", NULL);
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	/* display */
	prop= RNA_def_property(srna, "syntax_highlight", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "showsyntax", 0);
	RNA_def_property_ui_text(prop, "Syntax Highlight", "Syntax highlight for scripting.");
	RNA_def_property_ui_icon(prop, ICON_SYNTAX_OFF, 1);
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "word_wrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "wordwrap", 0);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_SpaceTextEditor_word_wrap_set");
	RNA_def_property_ui_text(prop, "Word Wrap", "Wrap words if there is not enough horizontal space.");
	RNA_def_property_ui_icon(prop, ICON_WORDWRAP_OFF, 1);
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "line_numbers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "showlinenrs", 0);
	RNA_def_property_ui_text(prop, "Line Numbers", "Show line numbers next to the text.");
	RNA_def_property_ui_icon(prop, ICON_LINENUMBERS_OFF, 1);
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "overwrite", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_ui_text(prop, "Overwrite", "Overwrite characters when typing rather than inserting them.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);
	
	prop= RNA_def_property(srna, "live_edit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_ui_text(prop, "Live Edit", "Run python while editing.");

	prop= RNA_def_property(srna, "tab_width", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tabnumber");
	RNA_def_property_range(prop, 2, 8);
	RNA_def_property_ui_text(prop, "Tab Width", "Number of spaces to display tabs with.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "font_size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "lheight");
	RNA_def_property_range(prop, 8, 32);
	RNA_def_property_ui_text(prop, "Font Size", "Font size to use for displaying the text.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	/* find */
	prop= RNA_def_property(srna, "find_all", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", ST_FIND_ALL);
	RNA_def_property_ui_text(prop, "Find All", "Search in all text datablocks, instead of only the active one.");

	prop= RNA_def_property(srna, "find_wrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", ST_FIND_WRAP);
	RNA_def_property_ui_text(prop, "Find Wrap", "Search again from the start of the file when reaching the end.");

	prop= RNA_def_property(srna, "find_text", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "findstr");
	RNA_def_property_ui_text(prop, "Find Text", "Text to search for with the find tool.");

	prop= RNA_def_property(srna, "replace_text", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "replacestr");
	RNA_def_property_ui_text(prop, "Replace Text", "Text to replace selected text with using the replace tool.");
}

static void rna_def_space_dopesheet(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem mode_items[] = {
		{SACTCONT_DOPESHEET, "DOPESHEET", 0, "DopeSheet", ""},
		{SACTCONT_ACTION, "ACTION", 0, "Action Editor", ""},
		{SACTCONT_SHAPEKEY, "SHAPEKEY", 0, "ShapeKey Editor", ""}, // XXX to be depreceated?
		{SACTCONT_GPENCIL, "GPENCIL", 0, "Grease Pencil", ""},
		{0, NULL, 0, NULL, NULL}};
		
	
	srna= RNA_def_struct(brna, "SpaceDopeSheetEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceAction");
	RNA_def_struct_ui_text(srna, "Space DopeSheet Editor", "DopeSheet space data.");
	
	/* mode */
	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, mode_items);
	RNA_def_property_ui_text(prop, "Mode", "Editing context being displayed.");
	
	/* display */
	prop= RNA_def_property(srna, "show_seconds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SACTION_DRAWTIME);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // XXX for now, only set with operator
	RNA_def_property_ui_text(prop, "Show Seconds", "Show timing in seconds not frames.");
	
	prop= RNA_def_property(srna, "show_cframe_indicator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SACTION_NODRAWCFRANUM);
	RNA_def_property_ui_text(prop, "Show Frame Number Indicator", "Show frame number beside the current frame indicator line.");
	
	prop= RNA_def_property(srna, "show_sliders", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SACTION_SLIDERS);
	RNA_def_property_ui_text(prop, "Show Sliders", "Show sliders beside F-Curve channels.");
	
	/* editing */
	prop= RNA_def_property(srna, "automerge_keyframes", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SACTION_NOTRANSKEYCULL);
	RNA_def_property_ui_text(prop, "AutoMerge Keyframes", "Show handles of Bezier control points.");
	
	// TODO... autosnap, dopesheet?
}

static void rna_def_space_graph(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem mode_items[] = {
		{SIPO_MODE_ANIMATION, "FCURVES", 0, "F-Curves", ""},
		{SIPO_MODE_DRIVERS, "DRIVERS", 0, "Drivers", ""},
		{0, NULL, 0, NULL, NULL}};
	
	
	srna= RNA_def_struct(brna, "SpaceGraphEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceIpo");
	RNA_def_struct_ui_text(srna, "Space Graph Editor", "Graph Editor space data.");
	
	/* mode */
	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, mode_items);
	RNA_def_property_ui_text(prop, "Mode", "Editing context being displayed.");
	
	/* display */
	prop= RNA_def_property(srna, "show_seconds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SIPO_DRAWTIME);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // XXX for now, only set with operator
	RNA_def_property_ui_text(prop, "Show Seconds", "Show timing in seconds not frames.");
	
	prop= RNA_def_property(srna, "show_cframe_indicator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SIPO_NODRAWCFRANUM);
	RNA_def_property_ui_text(prop, "Show Frame Number Indicator", "Show frame number beside the current frame indicator line.");
	
	prop= RNA_def_property(srna, "show_handles", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SIPO_NOHANDLES);
	RNA_def_property_ui_text(prop, "Show Handles", "Show handles of Bezier control points.");
	
	/* editing */
	prop= RNA_def_property(srna, "automerge_keyframes", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SIPO_NOTRANSKEYCULL);
	RNA_def_property_ui_text(prop, "AutoMerge Keyframes", "Show handles of Bezier control points.");
	
	// TODO... autosnap, dopesheet?
}

static void rna_def_space_nla(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "SpaceNLA", "Space");
	RNA_def_struct_sdna(srna, "SpaceNla");
	RNA_def_struct_ui_text(srna, "Space Nla Editor", "NLA editor space data.");
	
	/* display */
	prop= RNA_def_property(srna, "show_seconds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SNLA_DRAWTIME);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // XXX for now, only set with operator
	RNA_def_property_ui_text(prop, "Show Seconds", "Show timing in seconds not frames.");
	
	prop= RNA_def_property(srna, "show_cframe_indicator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SNLA_NODRAWCFRANUM);
	RNA_def_property_ui_text(prop, "Show Frame Number Indicator", "Show frame number beside the current frame indicator line.");
	
	prop= RNA_def_property(srna, "show_strip_curves", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", SNLA_NOSTRIPCURVES);
	RNA_def_property_ui_text(prop, "Show Control Curves", "Show influence curves on strips.");
	
	/* editing */
	// TODO... autosnap, dopesheet?
}

static void rna_def_console_line(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna = RNA_def_struct(brna, "ConsoleLine", NULL);
	RNA_def_struct_ui_text(srna, "Console Input", "Input line for the interactive console.");
	
	prop= RNA_def_property(srna, "line", PROP_STRING, PROP_NONE);
	RNA_def_property_string_funcs(prop, "rna_ConsoleLine_line_get", "rna_ConsoleLine_line_length", "rna_ConsoleLine_line_set");
	RNA_def_property_ui_text(prop, "Line", "Text in the line.");
	
	prop= RNA_def_property(srna, "current_character", PROP_INT, PROP_NONE); /* copied from text editor */
	RNA_def_property_int_sdna(prop, NULL, "cursor");
	RNA_def_property_int_funcs(prop, NULL, NULL, "rna_ConsoleLine_cursor_index_range");
	
}

static EnumPropertyItem console_type_items[] = {
	{CONSOLE_TYPE_PYTHON, "PYTHON", 0, "Python", ""},
	{CONSOLE_TYPE_REPORT, "REPORT", 0, "Report", ""},
	{0, NULL, 0, NULL, NULL}};
	
static void rna_def_space_console(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "SpaceConsole", "Space");
	RNA_def_struct_sdna(srna, "SpaceConsole");
	RNA_def_struct_ui_text(srna, "Space Console", "Interactive python console.");
	
	/* display */
	prop= RNA_def_property(srna, "font_size", PROP_INT, PROP_NONE); /* copied from text editor */
	RNA_def_property_int_sdna(prop, NULL, "lheight");
	RNA_def_property_range(prop, 8, 32);
	RNA_def_property_ui_text(prop, "Font Size", "Font size to use for displaying the text.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE, NULL);
	
	prop= RNA_def_property(srna, "console_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, console_type_items);
	RNA_def_property_ui_text(prop, "Type", "Console type.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE, NULL);
	
	/* reporting display */
	prop= RNA_def_property(srna, "show_report_debug", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "rpt_mask", CONSOLE_RPT_DEBUG);
	RNA_def_property_ui_text(prop, "Show Debug", "Display debug reporting info.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE_REPORT, NULL);
	
	prop= RNA_def_property(srna, "show_report_info", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "rpt_mask", CONSOLE_RPT_INFO);
	RNA_def_property_ui_text(prop, "Show Info", "Display general information.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE_REPORT, NULL);
	
	prop= RNA_def_property(srna, "show_report_operator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "rpt_mask", CONSOLE_RPT_OP);
	RNA_def_property_ui_text(prop, "Show Operator", "Display the operator log.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE_REPORT, NULL);
	
	prop= RNA_def_property(srna, "show_report_warn", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "rpt_mask", CONSOLE_RPT_WARN);
	RNA_def_property_ui_text(prop, "Show Warn", "Display warnings.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE_REPORT, NULL);
	
	prop= RNA_def_property(srna, "show_report_error", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "rpt_mask", CONSOLE_RPT_ERR);
	RNA_def_property_ui_text(prop, "Show Error", "Display error text.");
	RNA_def_property_update(prop, NC_CONSOLE | ND_CONSOLE_REPORT, NULL);

	
	
	prop= RNA_def_property(srna, "prompt", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Prompt", "Command line prompt.");
	RNA_def_struct_name_property(srna, prop);
	
	prop= RNA_def_property(srna, "history", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "history", NULL);
	RNA_def_property_struct_type(prop, "ConsoleLine");
	RNA_def_property_ui_text(prop, "History", "Command history.");
	
	prop= RNA_def_property(srna, "scrollback", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "scrollback", NULL);
	RNA_def_property_struct_type(prop, "ConsoleLine");
	RNA_def_property_ui_text(prop, "Output", "Command output.");
}

static void rna_def_fileselect_params(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem file_display_items[] = {
		{FILE_SHORTDISPLAY, "FILE_SHORTDISPLAY", ICON_SHORTDISPLAY, "Short List", "Display files as short list"},
		{FILE_LONGDISPLAY, "FILE_LONGDISPLAY", ICON_LONGDISPLAY, "Long List", "Display files as a detailed list"},
		{FILE_IMGDISPLAY, "FILE_IMGDISPLAY", ICON_IMGDISPLAY, "Thumbnails", "Display files as thumbnails"},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem file_sort_items[] = {
		{FILE_SORT_ALPHA, "FILE_SORT_ALPHA", ICON_SORTALPHA, "Sort alphabetically", "Sort the file list alphabetically."},
		{FILE_SORT_EXTENSION, "FILE_SORT_EXTENSION", ICON_SORTBYEXT, "Sort by extension", "Sort the file list by extension."},
		{FILE_SORT_TIME, "FILE_SORT_TIME", ICON_SORTTIME, "Sort by time", "Sort files by modification time."},
		{FILE_SORT_SIZE, "FILE_SORT_SIZE", ICON_SORTSIZE, "Sort by size", "Sort files by size."},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "FileSelectParams", NULL);
	RNA_def_struct_ui_text(srna, "File Select Parameters", "File Select Parameters.");

	prop= RNA_def_property(srna, "title", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "title");
	RNA_def_property_ui_text(prop, "Title", "Title for the file browser.");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);

	prop= RNA_def_property(srna, "directory", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "dir");
	RNA_def_property_ui_text(prop, "Directory", "Directory displayed in the file browser.");
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "file", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "file");
	RNA_def_property_ui_text(prop, "File Name", "Active file in the file browser.");
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "display", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "display");
	RNA_def_property_enum_items(prop, file_display_items);
	RNA_def_property_ui_text(prop, "Display Mode", "Display mode for the file list");
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "do_filter", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", FILE_FILTER);
	RNA_def_property_ui_text(prop, "Filter Files", "Enable filtering of files.");
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "hide_dot", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", FILE_HIDE_DOT);
	RNA_def_property_ui_text(prop, "Hide Dot Files", "Hide hidden dot files.");
	RNA_def_property_update(prop, NC_FILE | ND_FILELIST , NULL);

	prop= RNA_def_property(srna, "sort", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "sort");
	RNA_def_property_enum_items(prop, file_sort_items);
	RNA_def_property_ui_text(prop, "Sort", "");
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_image", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", IMAGEFILE);
	RNA_def_property_ui_text(prop, "Filter Images", "Show image files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_IMAGE, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_blender", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", BLENDERFILE);
	RNA_def_property_ui_text(prop, "Filter Blender", "Show .blend files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_BLEND, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_movie", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", MOVIEFILE);
	RNA_def_property_ui_text(prop, "Filter Movies", "Show movie files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_MOVIE, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_script", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", PYSCRIPTFILE);
	RNA_def_property_ui_text(prop, "Filter Script", "Show script files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_SCRIPT, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_font", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", FTFONTFILE);
	RNA_def_property_ui_text(prop, "Filter Fonts", "Show font files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_FONT, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_sound", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", SOUNDFILE);
	RNA_def_property_ui_text(prop, "Filter Sound", "Show sound files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_SOUND, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_text", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", TEXTFILE);
	RNA_def_property_ui_text(prop, "Filter Text", "Show text files.");
	RNA_def_property_ui_icon(prop, ICON_FILE_BLANK, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	prop= RNA_def_property(srna, "filter_folder", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filter", FOLDERFILE);
	RNA_def_property_ui_text(prop, "Filter Folder", "Show folders.");
	RNA_def_property_ui_icon(prop, ICON_FILE_FOLDER, 0);
	RNA_def_property_update(prop, NC_FILE | ND_PARAMS, NULL);

	
}

static void rna_def_space_filebrowser(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "SpaceFileBrowser", "Space");
	RNA_def_struct_sdna(srna, "SpaceFile");
	RNA_def_struct_ui_text(srna, "Space File Browser", "File browser space data.");

	prop= RNA_def_property(srna, "params", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "params");
	RNA_def_property_pointer_funcs(prop, NULL, "rna_SpaceFileBrowser_params_set", NULL);
	RNA_def_property_ui_text(prop, "Filebrowser Parameter", "Parameters and Settings for the Filebrowser.");

}

void RNA_def_space(BlenderRNA *brna)
{
	rna_def_space(brna);
	rna_def_space_image(brna);
	rna_def_space_sequencer(brna);
	rna_def_space_text(brna);
	rna_def_fileselect_params(brna);
	rna_def_space_filebrowser(brna);
	rna_def_space_outliner(brna);
	rna_def_background_image(brna);
	rna_def_space_3dview(brna);
	rna_def_space_buttons(brna);
	rna_def_space_dopesheet(brna);
	rna_def_space_graph(brna);
	rna_def_space_nla(brna);
	rna_def_space_console(brna);
	rna_def_console_line(brna);
}

#endif

