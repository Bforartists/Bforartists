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

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_scene_types.h"

/*
#include "BKE_writeffmpeg.h"
#include <libavcodec/avcodec.h> 
#include <libavformat/avformat.h>
*/

#include "WM_types.h"

/* prop_mode needs to be accessible from transform operator */
EnumPropertyItem prop_mode_items[] ={
	{PROP_SMOOTH, "SMOOTH", 0, "Smooth", ""},
	{PROP_SPHERE, "SPHERE", 0, "Sphere", ""},
	{PROP_ROOT, "ROOT", 0, "Root", ""},
	{PROP_SHARP, "SHARP", 0, "Sharp", ""},
	{PROP_LIN, "LINEAR", 0, "Linear", ""},
	{PROP_CONST, "CONSTANT", 0, "Constant", ""},
	{PROP_RANDOM, "RANDOM", 0, "Random", ""},
	{0, NULL, 0, NULL, NULL}};

#ifdef RNA_RUNTIME

#include "BKE_context.h"
#include "BKE_global.h"

PointerRNA rna_Scene_objects_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;

	/* we are actually iterating a Base list, so override get */
	return rna_pointer_inherit_refine(&iter->parent, &RNA_Object, ((Base*)internal->link)->object);
}

static void rna_Scene_layer_set(PointerRNA *ptr, const int *values)
{
	Scene *scene= (Scene*)ptr->data;
	int i, tot= 0;

	/* ensure we always have some layer selected */
	for(i=0; i<20; i++)
		if(values[i])
			tot++;
	
	if(tot==0)
		return;

	for(i=0; i<20; i++) {
		if(values[i]) scene->lay |= (1<<i);
		else scene->lay &= ~(1<<i);
	}
}

static void rna_Scene_start_frame_set(PointerRNA *ptr, int value)
{
	Scene *data= (Scene*)ptr->data;
	CLAMP(value, 1, data->r.efra);
	data->r.sfra= value;
}

static void rna_Scene_end_frame_set(PointerRNA *ptr, int value)
{
	Scene *data= (Scene*)ptr->data;
	CLAMP(value, data->r.sfra, MAXFRAME);
	data->r.efra= value;
}

static void rna_Scene_frame_update(bContext *C, PointerRNA *ptr)
{
	//Scene *scene= ptr->id.data;
	//update_for_newframe();
}

#else

void rna_def_sculpt(BlenderRNA  *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Sculpt", NULL);
	RNA_def_struct_nested(brna, srna, "Scene");
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

void rna_def_tool_settings(BlenderRNA  *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem uv_select_mode_items[] = {
		{UV_SELECT_VERTEX, "VERTEX", ICON_VERTEXSEL, "Vertex", "Vertex selection mode."},
		{UV_SELECT_EDGE, "EDGE", ICON_EDGESEL, "Edge", "Edge selection mode."},
		{UV_SELECT_FACE, "FACE", ICON_FACESEL, "Face", "Face selection mode."},
		{UV_SELECT_ISLAND, "ISLAND", ICON_LINKEDSEL, "Island", "Island selection mode."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem mesh_select_mode_items[] = {
		{SCE_SELECT_VERTEX, "VERTEX", ICON_VERTEXSEL, "Vertex", "Vertex selection mode."},
		{SCE_SELECT_EDGE, "EDGE", ICON_EDGESEL, "Edge", "Edge selection mode."},
		{SCE_SELECT_FACE, "FACE", ICON_FACESEL, "Face", "Face selection mode."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem snap_element_items[] = {
		{SCE_SNAP_MODE_VERTEX, "VERTEX", ICON_SNAP_VERTEX, "Vertex", "Snap to vertices."},
		{SCE_SNAP_MODE_EDGE, "EDGE", ICON_SNAP_EDGE, "Edge", "Snap to edges."},
		{SCE_SNAP_MODE_FACE, "FACE", ICON_SNAP_FACE, "Face", "Snap to faces."},
		{SCE_SNAP_MODE_VOLUME, "VOLUME", ICON_SNAP_VOLUME, "Volume", "Snap to volume."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem snap_mode_items[] = {
		{SCE_SNAP_TARGET_CLOSEST, "CLOSEST", 0, "Closest", "Snap closest point onto target."},
		{SCE_SNAP_TARGET_CENTER, "CENTER", 0, "Center", "Snap center onto target."},
		{SCE_SNAP_TARGET_MEDIAN, "MEDIAN", 0, "Median", "Snap median onto target."},
		{SCE_SNAP_TARGET_ACTIVE, "ACTIVE", 0, "Active", "Snap active onto target."},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "ToolSettings", NULL);
	RNA_def_struct_ui_text(srna, "Tool Settings", "");
	
	prop= RNA_def_property(srna, "sculpt", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Sculpt");
	RNA_def_property_ui_text(prop, "Sculpt", "");
	
	prop= RNA_def_property(srna, "vpaint", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "VPaint");
	RNA_def_property_ui_text(prop, "Vertex Paint", "");

	/* Transform */
	prop= RNA_def_property(srna, "proportional_editing", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "proportional", 0);
	RNA_def_property_ui_text(prop, "Proportional Editing", "Proportional editing mode.");

	prop= RNA_def_property(srna, "proportional_editing_falloff", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "prop_mode");
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Proportional Editing Falloff", "Falloff type for proportional editing mode.");

	prop= RNA_def_property(srna, "snap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "snap_flag", SCE_SNAP);
	RNA_def_property_ui_text(prop, "Snap", "Snap while Ctrl is held during transform.");
	RNA_def_property_ui_icon(prop, ICON_SNAP_GEAR, 1);

	prop= RNA_def_property(srna, "snap_align_rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "snap_flag", SCE_SNAP_ROTATE);
	RNA_def_property_ui_text(prop, "Snap Align Rotation", "Align rotation with the snapping target.");
	RNA_def_property_ui_icon(prop, ICON_SNAP_NORMAL, 0);

	prop= RNA_def_property(srna, "snap_element", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "snap_mode");
	RNA_def_property_enum_items(prop, snap_element_items);
	RNA_def_property_ui_text(prop, "Snap Element", "Type of element to snap to.");

	prop= RNA_def_property(srna, "snap_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "snap_target");
	RNA_def_property_enum_items(prop, snap_mode_items);
	RNA_def_property_ui_text(prop, "Snap Mode", "Which part to snap onto the target.");

	prop= RNA_def_property(srna, "snap_peel_object", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "snap_flag", SCE_SNAP_PEEL_OBJECT);
	RNA_def_property_ui_text(prop, "Snap Peel Object", "Consider objects as whole when finding volume center.");
	RNA_def_property_ui_icon(prop, ICON_SNAP_PEEL_OBJECT, 0);

	/* UV */
	prop= RNA_def_property(srna, "uv_selection_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "uv_selectmode");
	RNA_def_property_enum_items(prop, uv_select_mode_items);
	RNA_def_property_ui_text(prop, "UV Selection Mode", "UV selection and display mode.");

	prop= RNA_def_property(srna, "uv_sync_selection", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uv_flag", UV_SYNC_SELECTION);
	RNA_def_property_ui_text(prop, "UV Sync Selection", "Keep UV and edit mode mesh selection in sync.");
	RNA_def_property_ui_icon(prop, ICON_EDIT, 0);

	prop= RNA_def_property(srna, "uv_local_view", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uv_flag", UV_SHOW_SAME_IMAGE);
	RNA_def_property_ui_text(prop, "UV Local View", "Draw only faces with the currently displayed image assigned.");

	/* Mesh */
	prop= RNA_def_property(srna, "mesh_selection_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "selectmode");
	RNA_def_property_enum_items(prop, mesh_select_mode_items);
	RNA_def_property_ui_text(prop, "Mesh Selection Mode", "Mesh selection and display mode.");

	prop= RNA_def_property(srna, "vertex_group_weight", PROP_FLOAT, PROP_PERCENTAGE);
	RNA_def_property_float_sdna(prop, NULL, "vgroup_weight");
	RNA_def_property_ui_text(prop, "Vertex Group Weight", "Weight to assign in vertex groups.");

	/* Sculpt */
	rna_def_sculpt(brna);
}

void rna_def_scene_render_data(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem pixel_filter_items[] ={
		{R_FILTER_BOX, "BOX", 0, "Box", ""},
		{R_FILTER_TENT, "TENT", 0, "Tent", ""},
		{R_FILTER_QUAD, "QUADRATIC", 0, "Quadratic", ""},
		{R_FILTER_CUBIC, "CUBIC", 0, "Cubic", ""},
		{R_FILTER_CATROM, "CATMULLROM", 0, "Catmull-Rom", ""},
		{R_FILTER_GAUSS, "GAUSSIAN", 0, "Gaussian", ""},
		{R_FILTER_MITCH, "MITCHELL", 0, "Mitchell-Netravali", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem alpha_mode_items[] ={
		{R_ADDSKY, "SKY", 0, "Sky", "Transparent pixels are filled with sky color"},
		{R_ALPHAPREMUL, "PREMUL", 0, "Premultiplied", "Transparent RGB pixels are multiplied by the alpha channel"},
		{R_ALPHAKEY, "STRAIGHT", 0, "Straight Alpha", "Transparent RGB and alpha pixels are unmodified"},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem color_mode_items[] ={
		{R_PLANESBW, "BW", 0, "BW", "Images are saved with BW (grayscale) data"},
		{R_PLANES24, "RGB", 0, "RGB", "Images are saved with RGB (color) data"},
		{R_PLANES32, "RGBA", 0, "RGBA", "Images are saved with RGB and Alpha data (if supported)"},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem octree_resolution_items[] = {
		{64, "OCTREE_RES_64", 0, "64", ""},
		{128, "OCTREE_RES_128", 0, "128", ""},
		{256, "OCTREE_RES_256", 0, "256", ""},
		{512, "OCTREE_RES_512", 0, "512", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem raytrace_structure_items[] = {
		{R_RAYSTRUCTURE_HIER_BVH_BVH, "{R_RAYSTRUCTURE_HIER_BVH_BVH", 0, "BVH of BVH's", "Create a BVH of objects (each object has it own BVH)"},
		{R_RAYSTRUCTURE_HIER_BVH_OCTREE, "{R_RAYSTRUCTURE_HIER_BVH_OCTREE", 0, "BVH of octree", "Create a BVH of objects (each object has it own octree)"},
		{R_RAYSTRUCTURE_SINGLE_BVH, "{R_RAYSTRUCTURE_SINGLE_BVH", 0, "Single BVH", "BVH of all primitives (no instance support)"},
		{R_RAYSTRUCTURE_SINGLE_OCTREE, "{R_RAYSTRUCTURE_SINGLE_OCTREE", 0, "Octree", "Octree of all primitives (no instance support)"},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem raytrace_tree_type_items[] = {
		{R_RAYTRACE_TREE_BVH, "{R_RAYTRACE_TREE_BVH", 0, "BVH", "rayobject_bvh.c"},
		{R_RAYTRACE_TREE_BLIBVH, "{R_RAYTRACE_TREE_BLIBVH", 0, "BLIbvh", "rayobject_blibvh.c"},
		{R_RAYTRACE_TREE_BIH, "{R_RAYSTRUCTURE_SINGLE_BVH", 0, "BIH", "rayobject_bih.c"},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem fixed_oversample_items[] = {
		{5, "OVERSAMPLE_5", 0, "5", ""},
		{8, "OVERSAMPLE_8", 0, "8", ""},
		{11, "OVERSAMPLE_11", 0, "11", ""},
		{16, "OVERSAMPLE_16", 0, "16", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem field_order_items[] = {
		{0, "FIELDS_EVENFIRST", 0, "Even", "Even Fields First"},
		{R_ODDFIELD, "FIELDS_ODDFIRST", 0, "Odd", "Odd Fields First"},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem threads_mode_items[] = {
		{0, "THREADS_AUTO", 0, "Auto-detect", "Automatically determine the number of threads, based on CPUs"},
		{R_FIXED_THREADS, "THREADS_FIXED", 0, "Fixed", "Manually determine the number of threads"},
		{0, NULL, 0, NULL, NULL}};
	
	static EnumPropertyItem stamp_font_size_items[] = {
		{1, "STAMP_FONT_TINY", 0, "Tiny", ""},
		{2, "STAMP_FONT_SMALL", 0, "Small", ""},
		{3, "STAMP_FONT_MEDIUM", 0, "Medium", ""},
		{0, "STAMP_FONT_LARGE", 0, "Large", ""},
		{4, "STAMP_FONT_EXTRALARGE", 0, "Extra Large", ""},
		{0, NULL, 0, NULL, NULL}};
		
	
	static EnumPropertyItem image_type_items[] = {
		{R_FRAMESERVER, "FRAMESERVER", 0, "Frame Server", ""},
#ifdef WITH_FFMPEG
		{R_FFMPEG, "FFMPEG", 0, "FFMpeg", ""},
#endif
		{R_AVIRAW, "AVIRAW", 0, "AVI Raw", ""},
		{R_AVIJPEG, "AVIJPEG", 0, "AVI JPEG", ""},
#ifdef _WIN32
		{R_AVICODEC, "AVICODEC", 0, "AVI Codec", ""},
#endif
#ifdef WITH_QUICKTIME
		{R_QUICKTIME, "QUICKTIME", 0, "QuickTime", ""},
#endif
		{R_TARGA, "TARGA", 0, "Targa", ""},
		{R_RAWTGA, "RAWTARGA", 0, "Targa Raw", ""},
		{R_PNG, "PNG", 0, "PNG", ""},
		//{R_DDS, "DDS", 0, "DDS", ""}, // XXX not yet implemented
//#ifdef WITH_OPENJPEG
		{R_JP2, "JPEG2000", 0, "JPEG 2000", ""},
//#endif		
		{R_BMP, "BMP", 0, "BMP", ""},
		{R_JPEG90, "JPEG", 0, "JPEG", ""},
		{R_HAMX, "HAMX", 0, "HamX", ""},
		{R_IRIS, "IRIS", 0, "Iris", ""},
		{R_RADHDR, "RADHDR", 0, "Radiance HDR", ""},
		{R_CINEON, "CINEON", 0, "Cineon", ""},
		{R_DPX, "DPX", 0, "DPX", ""},
#ifdef __sgi
		{R_MOVIE, "MOVIE", 0, "Movie", ""},
#endif
//#ifdef WITH_OPENEXR
		{R_OPENEXR, "OPENEXR", 0, "OpenEXR", ""},
		{R_MULTILAYER, "MULTILAYER", 0, "MultiLayer", ""},
//#endif
		{R_TIFF, "TIFF", 0, "TIFF", ""},	// XXX only with G.have_libtiff
		{0, NULL, 0, NULL, NULL}};
		
//#ifdef WITH_OPENEXR	
	static EnumPropertyItem exr_codec_items[] = {
		{0, "NONE", 0, "None", ""},
		{1, "PXR24", 0, "Pxr24 (lossy)", ""},
		{2, "ZIP", 0, "ZIP (lossless)", ""},
		{3, "PIZ", 0, "PIZ (lossless)", ""},
		{4, "RLE", 0, "RLE (lossless)", ""},
		{0, NULL, 0, NULL, NULL}};
//#endif

//#ifdef WITH_OPENJPEG
	static EnumPropertyItem jp2_preset_items[] = {
		{0, "NO_PRESET", 0, "No Preset", ""},
		{1, "R_JPEG2K_CINE_PRESET", 0, "Cinema 24fps 2048x1080", ""},
		{2, "R_JPEG2K_CINE_PRESET|R_JPEG2K_CINE_48FPS", 0, "Cinema 48fps 2048x1080", ""},
		{3, "R_JPEG2K_CINE_PRESET", 0, "Cinema 24fps 4096x2160", ""},
		{4, "R_JPEG2K_CINE_PRESET", 0, "Cine-Scope 24fps 2048x858", ""},
		{5, "R_JPEG2K_CINE_PRESET|R_JPEG2K_CINE_48FPS", 0, "Cine-Scope 48fps 2048x858", ""},
		{6, "R_JPEG2K_CINE_PRESET", 0, "Cine-Flat 24fps 1998x1080", ""},
		{7, "R_JPEG2K_CINE_PRESET|R_JPEG2K_CINE_48FPS", 0, "Cine-Flat 48fps 1998x1080", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem jp2_depth_items[] = {
		{0, "8", 0, "8", ""},
		{R_JPEG2K_12BIT, "16", 0, "16", ""},
		{R_JPEG2K_16BIT, "32", 0, "32", ""},
		{0, NULL, 0, NULL, NULL}};
//#endif

/*
#ifdef WITH_FFMPEG
	static EnumPropertyItem ffmpeg_format_items[] = {
		{FFMPEG_MPEG1, "MPEG1", 0, "MPEG-1", ""},
		{FFMPEG_MPEG2, "MPEG2", 0, "MPEG-2", ""},
		{FFMPEG_MPEG4, "MPEG4", 0, "MPEG-4", ""},
		{FFMPEG_AVI, "AVI", 0, "Avi", ""},
		{FFMPEG_MOV, "QUICKTIME", 0, "Quicktime", ""},
		{FFMPEG_DV, "DV", 0, "DV", ""},
		{FFMPEG_H264, "H264", 0, "H264", ""},
		{FFMPEG_XVID, "XVID", 0, "XVid", ""},
		{FFMPEG_OGG, "OGG", 0, "OGG", ""},
		{FFMPEG_FLV, "FLASH", 0, "Flash", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem ffmpeg_codec_items[] = {
		{CODEC_ID_MPEG1VIDEO, "MPEG1", 0, "MPEG-1", ""},
		{CODEC_ID_MPEG2VIDEO, "MPEG2", 0, "MPEG-2", ""},
		{CODEC_ID_MPEG4, "MPEG4", 0, "MPEG-4(divx)", ""},
		{CODEC_ID_HUFFYUV, "HUFFYUV", 0, "HuffYUV", ""},
		{CODEC_ID_DVVIDEO, "DV", 0, "DV", ""},
		{CODEC_ID_H264, "H264", 0, "H264", ""},
		{CODEC_ID_XVID, "XVID", 0, "XVid", ""},
		{CODEC_ID_THEORA, "THEORA", 0, "OGG Theora", ""},
		{CODEC_ID_FLV1, "FLASH", 0, "FlashVideo1", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem ffmpeg_audio_codec_items[] = {
		{CODEC_ID_MP2, "MP2", 0, "MP2", ""},
		{CODEC_ID_MP3, "MP3", 0, "MP3", ""},
		{CODEC_ID_AC3, "AC3", 0, "AC3", ""},
		{CODEC_ID_AAC, "AAC", 0, "AAC", ""},
		{CODEC_ID_VORBIS, "VORBIS", 0, "Vorbis", ""},
		{CODEC_ID_PCM_S16LE, "PCM", 0, "PCM", ""},
		{0, NULL, 0, NULL, NULL}};
#endif
*/

	srna= RNA_def_struct(brna, "SceneRenderData", NULL);
	RNA_def_struct_sdna(srna, "RenderData");
	RNA_def_struct_nested(brna, srna, "Scene");
	RNA_def_struct_ui_text(srna, "Render Data", "Rendering settings for a Scene datablock.");
	
	prop= RNA_def_property(srna, "color_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "planes");
	RNA_def_property_enum_items(prop, color_mode_items);
	RNA_def_property_ui_text(prop, "Color Mode", "Choose BW for saving greyscale images, RGB for saving red, green and blue channels, AND RGBA for saving red, green, blue + alpha channels");
	
	prop= RNA_def_property(srna, "resolution_x", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "xsch");
	RNA_def_property_range(prop, 4, 10000);
	RNA_def_property_ui_text(prop, "Resolution X", "Number of horizontal pixels in the rendered image.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS|NC_OBJECT, NULL);
	
	prop= RNA_def_property(srna, "resolution_y", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ysch");
	RNA_def_property_range(prop, 4, 10000);
	RNA_def_property_ui_text(prop, "Resolution Y", "Number of vertical pixels in the rendered image.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS|NC_OBJECT, NULL);
	
	prop= RNA_def_property(srna, "resolution_percentage", PROP_INT, PROP_PERCENTAGE);
	RNA_def_property_int_sdna(prop, NULL, "size");
	RNA_def_property_ui_range(prop, 1, 100, 10, 1);
	RNA_def_property_ui_text(prop, "Resolution %", "Percentage scale for render resolution");
	
	prop= RNA_def_property(srna, "parts_x", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "xparts");
	RNA_def_property_range(prop, 1, 512);
	RNA_def_property_ui_text(prop, "Parts X", "Number of horizontal tiles to use while rendering.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "parts_y", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "yparts");
	RNA_def_property_range(prop, 1, 512);
	RNA_def_property_ui_text(prop, "Parts Y", "Number of vertical tiles to use while rendering.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "pixel_aspect_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xasp");
	RNA_def_property_range(prop, 1.0f, 200.0f);
	RNA_def_property_ui_text(prop, "Pixel Aspect X", "Horizontal aspect ratio - for anamorphic or non-square pixel output");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS|NC_OBJECT, NULL);
	
	prop= RNA_def_property(srna, "pixel_aspect_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "yasp");
	RNA_def_property_range(prop, 1.0f, 200.0f);
	RNA_def_property_ui_text(prop, "Pixel Aspect Y", "Vertical aspect ratio - for anamorphic or non-square pixel output");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS|NC_OBJECT, NULL);
	
	/* JPEG and AVI JPEG */
	
	prop= RNA_def_property(srna, "quality", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "quality");
	RNA_def_property_range(prop, 1, 100);
	RNA_def_property_ui_text(prop, "Quality", "Quality of JPEG images, AVI Jpeg and SGI movies.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	/* Tiff */
	
	prop= RNA_def_property(srna, "tiff_bit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_TIFF_16BIT);
	RNA_def_property_ui_text(prop, "16 Bit", "Save TIFF with 16 bits per channel");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	/* Cineon and DPX */
	
	prop= RNA_def_property(srna, "cineon_log", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_CINEON_LOG);
	RNA_def_property_ui_text(prop, "Log", "Convert to logarithmic color space");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "cineon_black", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "cineonblack");
	RNA_def_property_range(prop, 0, 1024);
	RNA_def_property_ui_text(prop, "B", "Log conversion reference blackpoint");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "cineon_white", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "cineonwhite");
	RNA_def_property_range(prop, 0, 1024);
	RNA_def_property_ui_text(prop, "W", "Log conversion reference whitepoint");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "cineon_gamma", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "cineongamma");
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "G", "Log conversion gamma");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

//#ifdef WITH_OPENEXR	
	/* OpenEXR */

	prop= RNA_def_property(srna, "exr_codec", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "quality");
	RNA_def_property_enum_items(prop, exr_codec_items);
	RNA_def_property_ui_text(prop, "Codec", "Codec settings for OpenEXR");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "exr_half", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_OPENEXR_HALF);
	RNA_def_property_ui_text(prop, "Half", "Use 16 bit floats instead of 32 bit floats per channel");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "exr_zbuf", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_OPENEXR_ZBUF);
	RNA_def_property_ui_text(prop, "Zbuf", "Save the z-depth per pixel (32 bit unsigned int zbuffer)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "exr_preview", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_PREVIEW_JPG);
	RNA_def_property_ui_text(prop, "Preview", "When rendering animations, save JPG preview images in same directory");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
//#endif

//#ifdef WITH_OPENJPEG
	/* Jpeg 2000 */

	prop= RNA_def_property(srna, "jpeg_preset", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "jp2_preset");
	RNA_def_property_enum_items(prop, jp2_preset_items);
	RNA_def_property_ui_text(prop, "Preset", "Use a DCI Standard preset for saving jpeg2000");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "jpeg_depth", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "jp2_depth");
	RNA_def_property_enum_items(prop, jp2_depth_items);
	RNA_def_property_ui_text(prop, "Depth", "Bit depth per channel");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "jpeg_ycc", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_JPEG2K_YCC);
	RNA_def_property_ui_text(prop, "YCC", "Save luminance-chrominance-chrominance channels instead of RGB colors");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
//#endif

#ifdef WITH_FFMPEG
	/* FFMPEG Video*/
	
	/*
	prop= RNA_def_property(srna, "ffmpeg_format", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "ffcodecdata.type");
	RNA_def_property_enum_items(prop, ffmpeg_format_items);
	RNA_def_property_ui_text(prop, "Format", "Output file format");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_codec", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "ffcodecdata.codec");
	RNA_def_property_enum_items(prop, ffmpeg_codec_items);
	RNA_def_property_ui_text(prop, "Codec", "FFMpeg codec to use");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	*/
	
	prop= RNA_def_property(srna, "ffmpeg_video_bitrate", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.video_bitrate");
	RNA_def_property_range(prop, 1, 14000);
	RNA_def_property_ui_text(prop, "Bitrate", "Video bitrate(kb/s)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_minrate", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.rc_min_rate");
	RNA_def_property_range(prop, 0, 9000);
	RNA_def_property_ui_text(prop, "Min Rate", "Rate control: min rate(kb/s)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_maxrate", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.rc_max_rate");
	RNA_def_property_range(prop, 1, 14000);
	RNA_def_property_ui_text(prop, "Max Rate", "Rate control: max rate(kb/s)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_muxrate", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.mux_rate");
	RNA_def_property_range(prop, 0, 100000000);
	RNA_def_property_ui_text(prop, "Mux Rate", "Mux rate (bits/s(!))");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_gopsize", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.gop_size");
	RNA_def_property_range(prop, 0, 100);
	RNA_def_property_ui_text(prop, "GOP Size", "Distance between key frames");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_buffersize", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.rc_buffer_size");
	RNA_def_property_range(prop, 0, 2000);
	RNA_def_property_ui_text(prop, "Buffersize", "Rate control: buffer size (kb)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_packetsize", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.mux_packet_size");
	RNA_def_property_range(prop, 0, 16384);
	RNA_def_property_ui_text(prop, "Mux Packet Size", "Mux packet size (byte)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_autosplit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ffcodecdata.flags", FFMPEG_AUTOSPLIT_OUTPUT);
	RNA_def_property_ui_text(prop, "Autosplit Output", "Autosplit output at 2GB boundary.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	/* FFMPEG Audio*/
	
	/*
	prop= RNA_def_property(srna, "ffmpeg_audio_codec", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "ffcodecdata.audio_codec");
	RNA_def_property_enum_items(prop, ffmpeg_audio_codec_items);
	RNA_def_property_ui_text(prop, Codec", "FFMpeg codec to use");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	*/
	
	prop= RNA_def_property(srna, "ffmpeg_audio_bitrate", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ffcodecdata.audio_bitrate");
	RNA_def_property_range(prop, 32, 384);
	RNA_def_property_ui_text(prop, "Bitrate", "Audio bitrate(kb/s)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "ffmpeg_multiplex_audio", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ffcodecdata.flags", FFMPEG_MULTIPLEX_AUDIO);
	RNA_def_property_ui_text(prop, "Multiplex Audio", "Interleave audio with the output video");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
#endif

	prop= RNA_def_property(srna, "fps", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "frs_sec");
	RNA_def_property_range(prop, 1, 120);
	RNA_def_property_ui_text(prop, "FPS", "Framerate, expressed in frames per second.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "fps_base", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "frs_sec_base");
	RNA_def_property_range(prop, 0.1f, 120.0f);
	RNA_def_property_ui_text(prop, "FPS Base", "Framerate base");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "dither_intensity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dither_intensity");
	RNA_def_property_range(prop, 0.0f, 2.0f);
	RNA_def_property_ui_text(prop, "Dither Intensity", "Amount of dithering noise added to the rendered image to break up banding.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "pixel_filter", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "filtertype");
	RNA_def_property_enum_items(prop, pixel_filter_items);
	RNA_def_property_ui_text(prop, "Pixel Filter", "Reconstruction filter used for combining anti-aliasing samples.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "filter_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "gauss");
	RNA_def_property_range(prop, 0.5f, 1.5f);
	RNA_def_property_ui_text(prop, "Filter Size", "Pixel width over which the reconstruction filter combines samples.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "alpha_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "alphamode");
	RNA_def_property_enum_items(prop, alpha_mode_items);
	RNA_def_property_ui_text(prop, "Alpha Mode", "Representation of alpha information in the RGBA pixels.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "octree_resolution", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "ocres");
	RNA_def_property_enum_items(prop, octree_resolution_items);
	RNA_def_property_ui_text(prop, "Octree Resolution", "Resolution of raytrace accelerator. Use higher resolutions for larger scenes.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "raytrace_structure", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "raystructure");
	RNA_def_property_enum_items(prop, raytrace_structure_items);
	RNA_def_property_ui_text(prop, "Raytrace Acceleration Structure", "Type of raytrace accelerator structure.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "raytrace_tree_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "raytrace_tree_type");
	RNA_def_property_enum_items(prop, raytrace_tree_type_items);
	RNA_def_property_ui_text(prop, "Raytrace tree type", "Type of raytrace accelerator structure.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "antialiasing", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_OSA);
	RNA_def_property_ui_text(prop, "Anti-Aliasing", "Render and combine multiple samples per pixel to prevent jagged edges.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "antialiasing_samples", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "osa");
	RNA_def_property_enum_items(prop, fixed_oversample_items);
	RNA_def_property_ui_text(prop, "Anti-Aliasing Samples", "Amount of anti-aliasing samples per pixel.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "fields", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_FIELDS);
	RNA_def_property_ui_text(prop, "Fields", "Render image to two fields per frame, for interlaced TV output.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "field_order", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, field_order_items);
	RNA_def_property_ui_text(prop, "Field Order", "Order of video fields. Select which lines get rendered first, to create smooth motion for TV output");
	
	prop= RNA_def_property(srna, "fields_still", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_FIELDSTILL);
	RNA_def_property_ui_text(prop, "Fields Still", "Disable the time difference between fields.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_shadows", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_SHADOW);
	RNA_def_property_ui_text(prop, "Render Shadows", "Calculate shadows while rendering.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_envmaps", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_ENVMAP);
	RNA_def_property_ui_text(prop, "Render Environment Maps", "Calculate environment maps while rendering.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_radiosity", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_RADIO);
	RNA_def_property_ui_text(prop, "Render Radiosity", "Calculate radiosity in a pre-process before rendering.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_sss", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_SSS);
	RNA_def_property_ui_text(prop, "Render SSS", "Calculate sub-surface scattering in materials rendering.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_raytracing", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_RAYTRACE);
	RNA_def_property_ui_text(prop, "Render Raytracing", "Pre-calculate the raytrace accelerator and render raytracing effects.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_textures", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "scemode", R_NO_TEX);
	RNA_def_property_ui_text(prop, "Render Textures", "Use textures to affect material properties.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "edge", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_EDGE);
	RNA_def_property_ui_text(prop, "Edge", "Create a toon outline around the edges of geometry");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "edge_intensity", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "edgeint");
	RNA_def_property_range(prop, 0, 255);
	RNA_def_property_ui_text(prop, "Edge Intensity", "Threshold for drawing outlines on geometry edges");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "edge_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "edgeR");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Edge Color", "");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "panorama", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_PANORAMA);
	RNA_def_property_ui_text(prop, "Panorama", "Render the scene with a cylindrical camera for pseudo-fisheye lens effects");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "threads", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "threads");
	RNA_def_property_range(prop, 1, 8);
	RNA_def_property_ui_text(prop, "Threads", "Number of CPU threads to use simultaneously while rendering (for multi-core/CPU systems)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "threads_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, threads_mode_items);
	RNA_def_property_ui_text(prop, "Threads Mode", "Determine the amount of render threads used");
	
	prop= RNA_def_property(srna, "motion_blur", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_MBLUR);
	RNA_def_property_ui_text(prop, "Motion Blur", "Use multi-sampled 3D scene motion blur (uses number of anti-aliasing samples).");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "border", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_BORDER);
	RNA_def_property_ui_text(prop, "Border", "Render a user-defined border region, within the frame size.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "crop_to_border", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_CROP);
	RNA_def_property_ui_text(prop, "Crop to Border", "Crop the rendered frame to the defined border size.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "placeholders", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_TOUCH);
	RNA_def_property_ui_text(prop, "Placeholders", "Create empty placeholder files while rendering frames (similar to Unix 'touch').");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "no_overwrite", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", R_NO_OVERWRITE);
	RNA_def_property_ui_text(prop, "No Overwrite", "Skip and don't overwrite existing files while rendering");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "do_composite", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_DOCOMP);
	RNA_def_property_ui_text(prop, "Do Composite", "Process the render result through the compositing pipeline");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "do_sequence", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_DOSEQ);
	RNA_def_property_ui_text(prop, "Do Sequence", "Process the render (and composited) result through the video sequence editor pipeline");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "file_extensions", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_EXTENSION);
	RNA_def_property_ui_text(prop, "File Extensions", "Add the file format extensions to the rendered file name (eg: filename + .jpg)");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "file_format", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "imtype");
	RNA_def_property_enum_items(prop, image_type_items);
	RNA_def_property_ui_text(prop, "File Format", "File format to save the rendered images as.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "free_image_textures", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_FREE_IMAGE);
	RNA_def_property_ui_text(prop, "Free Image Textures", "Free all image texture from memory after render, to save memory before compositing.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "save_buffers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_EXR_TILE_FILE);
	RNA_def_property_ui_text(prop, "Save Buffers","Save tiles for all RenderLayers and SceneNodes to files in the temp directory (saves memory, allows Full Sampling).");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "full_sample", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_FULL_SAMPLE);
	RNA_def_property_ui_text(prop, "Full Sample","Save for every anti-aliasing sample the entire RenderLayer results. This solves anti-aliasing issues with compositing");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "backbuf", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "bufflag", R_BACKBUF);
	RNA_def_property_ui_text(prop, "Back Buffer", "Render backbuffer image");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "output_path", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "pic");
	RNA_def_property_ui_text(prop, "Output Path", "Directory/name to save animations, # characters defines the position and length of frame numbers.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scemode", R_STAMP_INFO);
	RNA_def_property_ui_text(prop, "Stamp", "Embed metadata into the rendered image");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_time", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_TIME);
	RNA_def_property_ui_text(prop, "Stamp Time", "Include the current time in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_date", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_DATE);
	RNA_def_property_ui_text(prop, "Stamp Date", "Include the current date in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_frame", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_FRAME);
	RNA_def_property_ui_text(prop, "Stamp Frame", "Include the frame number in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_camera", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_CAMERA);
	RNA_def_property_ui_text(prop, "Stamp Camera", "Include the name of the active camera in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_scene", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_SCENE);
	RNA_def_property_ui_text(prop, "Stamp Scene", "Include the name of the active scene in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_note", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_NOTE);
	RNA_def_property_ui_text(prop, "Stamp Note", "Include a custom note in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_marker", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_MARKER);
	RNA_def_property_ui_text(prop, "Stamp Marker", "Include the name of the last marker in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_filename", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_FILENAME);
	RNA_def_property_ui_text(prop, "Stamp Filename", "Include the filename of the .blend file in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_sequence_strip", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_SEQSTRIP);
	RNA_def_property_ui_text(prop, "Stamp Sequence Strip", "Include the name of the foreground sequence strip in image metadata");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_note_text", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "stamp_udata");
	RNA_def_property_ui_text(prop, "Stamp Note Text", "Custom text to appear in the stamp note");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "render_stamp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "stamp", R_STAMP_DRAW);
	RNA_def_property_ui_text(prop, "Render Stamp", "Render the stamp info text in the rendered image");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_font_size", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "stamp_font_id");
	RNA_def_property_enum_items(prop, stamp_font_size_items);
	RNA_def_property_ui_text(prop, "Stamp Font Size", "Size of the font used when rendering stamp text");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_foreground", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "fg_stamp");
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Stamp Foreground", "Stamp text color");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "stamp_background", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "bg_stamp");
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Stamp Background", "Color to use behind stamp text");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
}

void RNA_def_scene(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Scene", "ID");
	RNA_def_struct_ui_text(srna, "Scene", "Scene consisting objects and defining time and render related settings.");
	RNA_def_struct_ui_icon(srna, ICON_SCENE_DATA);
	RNA_def_struct_clear_flag(srna, STRUCT_ID_REFCOUNT);

	prop= RNA_def_property(srna, "camera", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Camera", "Active camera used for rendering the scene.");

	prop= RNA_def_property(srna, "world", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "World", "World used for rendering the scene.");

	prop= RNA_def_property(srna, "cursor_location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "cursor");
	RNA_def_property_ui_text(prop, "Cursor Location", "3D cursor location.");
	RNA_def_property_ui_range(prop, -10000.0, 10000.0, 10, 4);

	prop= RNA_def_property(srna, "objects", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "base", NULL);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Objects", "");
	RNA_def_property_collection_funcs(prop, 0, 0, 0, "rna_Scene_objects_get", 0, 0, 0, 0, 0);

	prop= RNA_def_property(srna, "visible_layers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "lay", 1);
	RNA_def_property_array(prop, 20);
	RNA_def_property_ui_text(prop, "Visible Layers", "Layers visible when rendering the scene.");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_Scene_layer_set");

	prop= RNA_def_property(srna, "current_frame", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.cfra");
	RNA_def_property_range(prop, MINFRAME, MAXFRAME);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_SCENE|ND_FRAME, "rna_Scene_frame_update");
	
	prop= RNA_def_property(srna, "start_frame", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.sfra");
	RNA_def_property_int_funcs(prop, NULL, "rna_Scene_start_frame_set", NULL);
	RNA_def_property_ui_text(prop, "Start Frame", "");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "end_frame", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.efra");
	RNA_def_property_int_funcs(prop, NULL, "rna_Scene_end_frame_set", NULL);
	RNA_def_property_ui_text(prop, "End Frame", "");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "frame_step", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "frame_step");
	RNA_def_property_ui_text(prop, "Frame Step", "Number of frames to skip forward while rendering/playing back each frame");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "stamp_note", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "r.stamp_udata");
	RNA_def_property_ui_text(prop, "Stamp Note", "User define note for the render stamping.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "nodetree", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Node Tree", "Compositing node tree.");
	
	prop= RNA_def_property(srna, "sequence_editor", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ed");
	RNA_def_property_struct_type(prop, "SequenceEditor");
	RNA_def_property_ui_text(prop, "Sequence Editor", "");
	
	prop= RNA_def_property(srna, "keyingsets", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "keyingsets", NULL);
	RNA_def_property_struct_type(prop, "KeyingSet");
	RNA_def_property_ui_text(prop, "Keying Sets", "Keying Sets for this Scene.");
	
	prop= RNA_def_property(srna, "active_keyingset", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Active Keying Set", "Current Keying Set index.");

	prop= RNA_def_property(srna, "tool_settings", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "toolsettings");
	RNA_def_property_struct_type(prop, "ToolSettings");
	RNA_def_property_ui_text(prop, "Tool Settings", "");

	prop= RNA_def_property(srna, "render_data", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "r");
	RNA_def_property_struct_type(prop, "SceneRenderData");
	RNA_def_property_ui_text(prop, "Render Data", "");

	prop= RNA_def_property(srna, "timeline_markers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "markers", NULL);
	RNA_def_property_struct_type(prop, "TimelineMarker");
	RNA_def_property_ui_text(prop, "Timeline Markers", "Markers used in all timelines for the current scene.");

	rna_def_tool_settings(brna);
	rna_def_scene_render_data(brna);
}

#endif

