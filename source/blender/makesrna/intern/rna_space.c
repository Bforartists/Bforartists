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

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_view3d_types.h"

#include "WM_types.h"

EnumPropertyItem space_type_items[] = {
	{SPACE_EMPTY, "EMPTY", "Empty", ""},
	{SPACE_VIEW3D, "VIEW_3D", "3D View", ""},
	{SPACE_IPO, "GRAPH_EDITOR", "Graph Editor", ""},
	{SPACE_OUTLINER, "OUTLINER", "Outliner", ""},
	{SPACE_BUTS, "BUTTONS_WINDOW", "Buttons Window", ""},
	{SPACE_FILE, "FILE_BROWSER", "File Browser", ""},
	{SPACE_IMAGE, "IMAGE_EDITOR", "Image Editor", ""},
	{SPACE_INFO, "USER_PREFERENCES", "User Preferences", ""},
	{SPACE_SEQ, "SEQUENCE_EDITOR", "Sequence Editor", ""},
	{SPACE_TEXT, "TEXT_EDITOR", "Text Editor", ""},
	//{SPACE_IMASEL, "IMAGE_BROWSER", "Image Browser", ""},
	{SPACE_SOUND, "AUDIO_WINDOW", "Audio Window", ""},
	{SPACE_ACTION, "DOPESHEET_EDITOR", "DopeSheet Editor", ""},
	{SPACE_NLA, "NLA_EDITOR", "NLA Editor", ""},
	{SPACE_SCRIPT, "SCRIPTS_WINDOW", "Scripts Window", ""},
	{SPACE_TIME, "TIMELINE", "Timeline", ""},
	{SPACE_NODE, "NODE_EDITOR", "Node Editor", ""},
	{0, NULL, NULL, NULL}};

#ifdef RNA_RUNTIME

#include "DNA_scene_types.h"

#include "BKE_brush.h"
#include "BKE_context.h"

static StructRNA* rna_Space_refine(struct PointerRNA *ptr)
{
	SpaceLink *space= (SpaceLink*)ptr->data;

	switch(space->spacetype) {
		case SPACE_VIEW3D:
			return &RNA_Space3DView;
		/*case SPACE_IPO:
			return &RNA_SpaceGraphEditor;
		*/
		case SPACE_OUTLINER:
			return &RNA_SpaceOutliner;
		case SPACE_BUTS:
			return &RNA_SpaceButtonsWindow;
		/* case SPACE_FILE:
			return &RNA_SpaceFileBrowser;*/
		case SPACE_IMAGE:
			return &RNA_SpaceImageEditor;
		/*case SPACE_INFO:
			return &RNA_SpaceUserPreferences;
		case SPACE_SEQ:
			return &RNA_SpaceSequenceEditor;*/
		case SPACE_TEXT:
			return &RNA_SpaceTextEditor;
		//case SPACE_IMASEL:
		//	return &RNA_SpaceImageBrowser;
		/*case SPACE_SOUND:
			return &RNA_SpaceAudioWindow;
		case SPACE_ACTION:
			return &RNA_SpaceDopeSheetEditor;
		case SPACE_NLA:
			return &RNA_SpaceNLAEditor;
		case SPACE_SCRIPT:
			return &RNA_SpaceScriptsWindow;
		case SPACE_TIME:
			return &RNA_SpaceTimeline;
		case SPACE_NODE:
			return &RNA_SpaceNodeEditor;*/
		default:
			return &RNA_Space;
	}
}

static PointerRNA rna_SpaceImage_uvedit_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_SpaceUVEditor, ptr->data);
}

static void rna_SpaceImage_paint_update(bContext *C, PointerRNA *ptr)
{
	Scene *scene= CTX_data_scene(C);

	if(scene)
		brush_check_exists(&scene->toolsettings->imapaint.brush);
}

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

#if 0
	static EnumPropertyItem select_mode_items[] = {
		{SI_SELECT_VERTEX, "VERTEX", "Vertex", "Vertex selection mode."},
		//{SI_SELECT_EDGE, "Edge", "Edge", "Edge selection mode."},
		{SI_SELECT_FACE, "FACE", "Face", "Face selection mode."},
		{SI_SELECT_ISLAND, "ISLAND", "Island", "Island selection mode."},
		{0, NULL, NULL, NULL}};
#endif

	static EnumPropertyItem sticky_mode_items[] = {
		{SI_STICKY_DISABLE, "DISABLED", "Disabled", "Sticky vertex selection disabled."},
		{SI_STICKY_LOC, "SHARED_LOCATION", "SHARED_LOCATION", "Select UVs that are at the same location and share a mesh vertex."},
		{SI_STICKY_VERTEX, "SHARED_VERTEX", "SHARED_VERTEX", "Select UVs that share mesh vertex, irrespective if they are in the same location."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem dt_uv_items[] = {
		{SI_UVDT_OUTLINE, "OUTLINE", "Outline", "Draw white edges with black outline."},
		{SI_UVDT_DASH, "DASH", "Dash", "Draw dashed black-white edges."},
		{SI_UVDT_BLACK, "BLACK", "Black", "Draw black edges."},
		{SI_UVDT_WHITE, "WHITE", "White", "Draw white edges."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem dt_uvstretch_items[] = {
		{SI_UVDT_STRETCH_ANGLE, "ANGLE", "Angle", "Angular distortion between UV and 3D angles."},
		{SI_UVDT_STRETCH_AREA, "AREA", "Area", "Area distortion between UV and 3D faces."},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "SpaceUVEditor", NULL);
	RNA_def_struct_sdna(srna, "SpaceImage");
	RNA_def_struct_nested(brna, srna, "SpaceImageEditor");
	RNA_def_struct_ui_text(srna, "Space UV Editor", "UV editor data for the image editor space.");

	/* selection */
	/*prop= RNA_def_property(srna, "selection_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "selectmode");
	RNA_def_property_enum_items(prop, select_mode_items);
	RNA_def_property_ui_text(prop, "Selection Mode", "UV selection and display mode.");*/

	prop= RNA_def_property(srna, "sticky_selection_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "sticky");
	RNA_def_property_enum_items(prop, sticky_mode_items);
	RNA_def_property_ui_text(prop, "Sticky Selection Mode", "Automatically select also UVs sharing the same vertex as the ones being selected.");

	/* drawing */
	prop= RNA_def_property(srna, "edge_draw_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "dt_uv");
	RNA_def_property_enum_items(prop, dt_uv_items);
	RNA_def_property_ui_text(prop, "Edge Draw Type", "Draw type for drawing UV edges.");

	prop= RNA_def_property(srna, "draw_smooth_edges", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_SMOOTH_UV);
	RNA_def_property_ui_text(prop, "Draw Smooth Edges", "Draw UV edges anti-aliased.");

	prop= RNA_def_property(srna, "draw_stretch", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAW_STRETCH);
	RNA_def_property_ui_text(prop, "Draw Stretch", "Draw faces colored according to the difference in shape between UVs and their 3D coordinates (blue for low distortion, red for high distortion).");

	prop= RNA_def_property(srna, "draw_stretch_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "dt_uvstretch");
	RNA_def_property_enum_items(prop, dt_uvstretch_items);
	RNA_def_property_ui_text(prop, "Draw Stretch Type", "Type of stretch to draw.");

	prop= RNA_def_property(srna, "draw_modified_edges", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "dt_uvstretch");
	RNA_def_property_enum_items(prop, dt_uvstretch_items);
	RNA_def_property_ui_text(prop, "Draw Modified Edges", "Draw edges from the final mesh after object modifier evaluation.");

	/*prop= RNA_def_property(srna, "local_view", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_LOCAL_UV);
	RNA_def_property_ui_text(prop, "Local View", "Draw only faces with the currently displayed image assigned.");*/

	prop= RNA_def_property(srna, "normalized_coordinates", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_COORDFLOATS);
	RNA_def_property_ui_text(prop, "Normalized Coordinates", "Display UV coordinates from 0.0 to 1.0 rather than in pixels.");

	/* todo: move edge and face drawing options here from G.f */

	/* editing */
	/*prop= RNA_def_property(srna, "sync_selection", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_SYNC_UVSEL);
	RNA_def_property_ui_text(prop, "Sync Selection", "Keep UV and edit mode mesh selection in sync.");*/

	prop= RNA_def_property(srna, "snap_to_pixels", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_PIXELSNAP);
	RNA_def_property_ui_text(prop, "Snap to Pixels", "Snap UVs to pixel locations while editing.");

	prop= RNA_def_property(srna, "constrain_to_image_bounds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_CLIP_UV);
	RNA_def_property_ui_text(prop, "Constrain to Image Bounds", "Constraint to stay within the image bounds while editing.");

	prop= RNA_def_property(srna, "live_unwrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_LIVE_UNWRAP);
	RNA_def_property_ui_text(prop, "Live Unwrap", "Continuously unwrap the selected UV island while transforming pinned vertices.");
}

static void rna_def_space_outliner(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem display_mode_items[] = {
		{0, "ALL_SCENES", "All Scenes", ""},
		{1, "CURRENT_SCENE", "Current Scene", ""},
		{2, "VISIBLE_LAYERS", "Visible Layers", ""},
		{3, "SELECTED", "Selected", ""},
		{4, "ACTIVE", "Active", ""},
		{5, "SAME_TYPES", "Same Types", ""},
		{6, "GROUPS", "Groups", ""},
		{7, "LIBRARIES", "Libraries", ""},
		{10, "SEQUENCE", "Sequence", ""},
		{11, "DATABLOCKS", "Datablocks", ""},
		{12, "USER_PREFERENCES", "User Preferences", ""},
		{0, NULL, NULL, NULL}};

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
		{OB_BOUNDBOX, "BOUNDBOX", "Bounding Box", "Display the object's local bounding boxes only"},
		{OB_WIRE, "WIREFRAME", "Wireframe", "Display the object as wire edges"},
		{OB_SOLID, "SOLID", "Solid", "Display the object solid, lit with default OpenGL lights"},
		{OB_SHADED, "SHADED", "Shaded", "Display the object solid, with preview shading interpolated at vertices"},
		{OB_TEXTURE, "TEXTURED", "Textured", "Display the object solid, with face-assigned textures"},
		{0, NULL, NULL, NULL}};
		
	static EnumPropertyItem pivot_items[] = {
		{V3D_CENTER, "BOUNDING_BOX_CENTER", "Bounding Box Center", ""},
		{V3D_CURSOR, "CURSOR", "3D Cursor", ""},
		{V3D_LOCAL, "INDIVIDUAL_CENTERS", "Individual Centers", ""},
		{V3D_CENTROID, "MEDIAN_POINT", "Median Point", ""},
		{V3D_ACTIVE, "ACTIVE_ELEMENT", "Active Element", ""},
		{0, NULL, NULL, NULL}};
		
	static EnumPropertyItem transform_orientation_items[] = {
		{V3D_MANIP_GLOBAL, "ORIENT_GLOBAL", "Global", "Align the transformation axes to world space"},
		{V3D_MANIP_LOCAL, "ORIENT_LOCAL", "Local", "Align the transformation axes to the selected objects' local space"},
		{V3D_MANIP_NORMAL, "ORIENT_NORMAL", "Normal", "Align the transformation axes to average normal of selected elements (bone Y axis for pose mode)"},
		{V3D_MANIP_VIEW, "ORIENT_VIEW", "View", "Align the transformation axes to the window"},
		{V3D_MANIP_CUSTOM, "ORIENT_CUSTOM", "Custom", "Use a custom transform orientation"},
		{0, NULL, NULL, NULL}};

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
	
	prop= RNA_def_property(srna, "clip_start", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "near");
	RNA_def_property_range(prop, 0.0f, FLT_MAX);
	RNA_def_property_ui_text(prop, "Clip Start", "3D View near clipping distance.");

	prop= RNA_def_property(srna, "clip_end", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "far");
	RNA_def_property_range(prop, 1.0f, FLT_MAX);
	RNA_def_property_ui_text(prop, "Clip End", "3D View far clipping distance.");
	
	prop= RNA_def_property(srna, "grid_spacing", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "grid");
	RNA_def_property_ui_text(prop, "Grid Spacing", "The distance between 3D View grid lines.");
	RNA_def_property_range(prop, 0.0f, FLT_MAX);
	
	prop= RNA_def_property(srna, "grid_lines", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gridlines");
	RNA_def_property_ui_text(prop, "Grid Lines", "The number of grid lines to display in perspective view.");
	RNA_def_property_range(prop, 0, 1024);
	
	prop= RNA_def_property(srna, "grid_subdivisions", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gridsubdiv");
	RNA_def_property_ui_text(prop, "Grid Subdivisions", "The number of subdivisions between grid lines.");
	RNA_def_property_range(prop, 1, 1024);
	
	prop= RNA_def_property(srna, "display_floor", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_FLOOR);
	RNA_def_property_ui_text(prop, "Display Grid Floor", "Show the ground plane grid in perspective view.");
	
	prop= RNA_def_property(srna, "display_x_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_X);
	RNA_def_property_ui_text(prop, "Display X Axis", "Show the X axis line in perspective view.");
	
	prop= RNA_def_property(srna, "display_y_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_Y);
	RNA_def_property_ui_text(prop, "Display Y Axis", "Show the Y axis line in perspective view.");
	
	prop= RNA_def_property(srna, "display_z_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gridflag", V3D_SHOW_Z);
	RNA_def_property_ui_text(prop, "Display Z Axis", "Show the Z axis line in perspective view.");
	
	prop= RNA_def_property(srna, "outline_selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", V3D_SELECT_OUTLINE);
	RNA_def_property_ui_text(prop, "Outline Selected", "Show an outline highlight around selected objects in non-wireframe views.");
	
	prop= RNA_def_property(srna, "all_object_centers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", V3D_DRAW_CENTERS);
	RNA_def_property_ui_text(prop, "All Object Centers", "Show the object center dot for all (selected and unselected) objects.");

	prop= RNA_def_property(srna, "relationship_lines", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", V3D_HIDE_HELPLINES);
	RNA_def_property_ui_text(prop, "Relationship Lines", "Show dashed lines indicating parent or constraint relationships.");
	
	prop= RNA_def_property(srna, "textured_solid", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag2", V3D_SOLID_TEX);
	RNA_def_property_ui_text(prop, "Textured Solid", "Display face-assigned textures in solid view");
	
	prop= RNA_def_property(srna, "pivot_point", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "around");
	RNA_def_property_enum_items(prop, pivot_items);
	RNA_def_property_ui_text(prop, "Pivot Point", "Pivot center for rotation/scaling.");
	
	prop= RNA_def_property(srna, "manipulator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twflag", V3D_USE_MANIPULATOR);
	RNA_def_property_ui_text(prop, "Manipulator", "Use a 3D manipulator widget for controlling transforms.");
	
	prop= RNA_def_property(srna, "manipulator_translate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twtype", V3D_MANIP_TRANSLATE);
	RNA_def_property_ui_text(prop, "Manipulator Translate", "Use the manipulator for movement transformations.");
	
	prop= RNA_def_property(srna, "manipulator_rotate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twtype", V3D_MANIP_ROTATE);
	RNA_def_property_ui_text(prop, "Manipulator Rotate", "Use the manipulator for rotation transformations.");
	
	prop= RNA_def_property(srna, "manipulator_scale", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "twtype", V3D_MANIP_SCALE);
	RNA_def_property_ui_text(prop, "Manipulator Scale", "Use the manipulator for scale transformations.");
	
	prop= RNA_def_property(srna, "transform_orientation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "twmode");
	RNA_def_property_enum_items(prop, transform_orientation_items);
	RNA_def_property_ui_text(prop, "Transform Orientation", "The alignment of manipulator handles.");
	
}

static void rna_def_space_buttons(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem buttons_context_items[] = {
		{BCONTEXT_SCENE, "SCENE", "Scene", ""},
		{BCONTEXT_WORLD, "WORLD", "World", ""},
		{BCONTEXT_OBJECT, "OBJECT", "Object", ""},
		{BCONTEXT_DATA, "DATA", "Data", ""},
		{BCONTEXT_MATERIAL, "MATERIAL", "Material", ""},
		{BCONTEXT_TEXTURE, "TEXTURE", "Texture", ""},
		{BCONTEXT_PARTICLE, "PARTICLE", "Particle", ""},
		{BCONTEXT_PHYSICS, "PHYSICS", "Physics", ""},
		{BCONTEXT_GAME, "GAME", "Game", ""},
		{BCONTEXT_BONE, "BONE", "Bone", ""},
		{BCONTEXT_MODIFIER, "MODIFIER", "Modifier", ""},
		{BCONTEXT_SEQUENCER, "SEQUENCER", "Sequencer", ""},
		{BCONTEXT_CONSTRAINT, "CONSTRAINT", "Constraint", ""},
		{0, NULL, NULL, NULL}};
		
	static EnumPropertyItem panel_alignment_items[] = {
		{1, "HORIZONTAL", "Horizontal", ""},
		{2, "VERTICAL", "Vertical", ""},
		{0, NULL, NULL, NULL}};
		
	srna= RNA_def_struct(brna, "SpaceButtonsWindow", "Space");
	RNA_def_struct_sdna(srna, "SpaceButs");
	RNA_def_struct_ui_text(srna, "Buttons Space", "Buttons Window space data");
	
	prop= RNA_def_property(srna, "buttons_context", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mainb");
	RNA_def_property_enum_items(prop, buttons_context_items);
	RNA_def_property_ui_text(prop, "Buttons Context", "The type of active data to display and edit in the buttons window");
	
	prop= RNA_def_property(srna, "panel_alignment", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "align");
	RNA_def_property_enum_items(prop, panel_alignment_items);
	RNA_def_property_ui_text(prop, "Panel Alignment", "Arrangement of the panels within the buttons window");
}

static void rna_def_space_image(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem draw_channels_items[] = {
		{0, "COLOR", "Color", "Draw image with RGB colors."},
		{SI_USE_ALPHA, "COLOR_ALPHA", "Color and Alpha", "Draw image with RGB colors and alpha transparency."},
		{SI_SHOW_ALPHA, "ALPHA", "Alpha", "Draw alpha transparency channel."},
		{SI_SHOW_ZBUF, "Z_BUFFER", "Z-Buffer", "Draw Z-buffer associated with image (mapped from camera clip start to end)."},
		{SI_COLOR_CORRECTION, "COLOR_CORRECTED", "Color Corrected", "Display color corrected image."},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "SpaceImageEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceImage");
	RNA_def_struct_ui_text(srna, "Space Image Editor", "Image and UV editor space data.");

	/* image */
	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Image", "Image displayed and edited in this space.");

	prop= RNA_def_property(srna, "image_user", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "iuser");
	RNA_def_property_ui_text(prop, "Image User", "Parameters defining which layer, pass and frame of the image is displayed.");

	prop= RNA_def_property(srna, "curves", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "cumap");
	RNA_def_property_ui_text(prop, "Curves", "Color curve mapping to use for displaying the image.");

	prop= RNA_def_property(srna, "image_pin", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "pin", 0);
	RNA_def_property_ui_text(prop, "Image Pin", "Display current image regardless of object selection.");

	/* image draw */
	prop= RNA_def_property(srna, "draw_repeated", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAW_TILE);
	RNA_def_property_ui_text(prop, "Draw Repeated", "Draw the image repeated outside of the main view.");

	prop= RNA_def_property(srna, "draw_channels", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "flag");
	RNA_def_property_enum_items(prop, draw_channels_items);
	RNA_def_property_ui_text(prop, "Draw Channels", "Channels of the image to draw.");

	/* uv */
	prop= RNA_def_property(srna, "uv_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "SpaceUVEditor");
	RNA_def_property_pointer_funcs(prop, "rna_SpaceImage_uvedit_get", NULL);
	RNA_def_property_ui_text(prop, "UV Editor", "UV editor settings.");
	
	/* paint */
	prop= RNA_def_property(srna, "image_painting", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SI_DRAWTOOL);
	RNA_def_property_ui_text(prop, "Image Painting", "Enable image painting mode.");
	RNA_def_property_update(prop, 0, "rna_SpaceImage_paint_update");

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
	RNA_def_property_ui_text(prop, "Update Automatically", "Update other affected window spaces automatically to reflect changes during interactive operations such as transform.");

	rna_def_space_image_uv(brna);
}

static void rna_def_space_text(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem font_size_items[] = {
		{12, "SCREEN_12", "Screen 12", ""},
		{15, "SCREEN_15", "Screen 15", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "SpaceTextEditor", "Space");
	RNA_def_struct_sdna(srna, "SpaceText");
	RNA_def_struct_ui_text(srna, "Space Text Editor", "Text editor space data.");

	/* text */
	prop= RNA_def_property(srna, "text", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Text", "Text displayed and edited in this space.");
	RNA_def_property_pointer_funcs(prop, NULL, "rna_SpaceTextEditor_text_set");
	RNA_def_property_update(prop, NC_TEXT|NA_EDITED, NULL);

	/* display */
	prop= RNA_def_property(srna, "syntax_highlight", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "showsyntax", 0);
	RNA_def_property_ui_text(prop, "Syntax Highlight", "Syntax highlight for scripting.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "word_wrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "wordwrap", 0);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_SpaceTextEditor_word_wrap_set");
	RNA_def_property_ui_text(prop, "Word Wrap", "Wrap words if there is not enough horizontal space.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "line_numbers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "showlinenrs", 0);
	RNA_def_property_ui_text(prop, "Line Numbers", "Show line numbers next to the text.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "overwrite", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_ui_text(prop, "Overwrite", "Overwrite characters when typing rather than inserting them.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "tab_width", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tabnumber");
	RNA_def_property_range(prop, 2, 8);
	RNA_def_property_ui_text(prop, "Tab Width", "Number of spaces to display tabs with.");
	RNA_def_property_update(prop, NC_TEXT|ND_DISPLAY, NULL);

	prop= RNA_def_property(srna, "font_size", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "lheight");
	RNA_def_property_enum_items(prop, font_size_items);
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

void RNA_def_space(BlenderRNA *brna)
{
	rna_def_space(brna);
	rna_def_space_image(brna);
	rna_def_space_text(brna);
	rna_def_space_outliner(brna);
	rna_def_background_image(brna);
	rna_def_space_3dview(brna);
	rna_def_space_buttons(brna);
}

#endif

