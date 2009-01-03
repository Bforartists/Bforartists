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

#include <float.h>
#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_texture_types.h"

#ifdef RNA_RUNTIME

#else

void rna_def_environment_map(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_source_items[] = {
		{ENV_STATIC, "STATIC", "Static", ""},
		{ENV_ANIM, "ANIMATED", "Animated", ""},
		{ENV_LOAD, "LOAD", "Load", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_type_items[] = {
		{ENV_CUBE, "CUBE", "Cube", "Use environment map with six cube sides."},
		{ENV_PLANE, "PLANE", "Plane", "Only one side is rendered, with Z axis pointing in direction of image."},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "EnvironmentMap", NULL);
	RNA_def_struct_sdna(srna, "EnvMap");
	RNA_def_struct_ui_text(srna, "EnvironmentMap", "DOC_BROKEN");
	
	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ima");
	RNA_def_property_struct_type(prop, "Image");
	RNA_def_property_ui_text(prop, "Image", "");

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, prop_type_items);
	RNA_def_property_ui_text(prop, "Type", "");

	prop= RNA_def_property(srna, "source", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "stype");
	RNA_def_property_enum_items(prop, prop_source_items);
	RNA_def_property_ui_text(prop, "Source", "");

	prop= RNA_def_property(srna, "clip_start", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "clipsta");
	RNA_def_property_range(prop, 0.01, FLT_MAX);
	RNA_def_property_ui_range(prop, 0.01, 50, 100, 2);
	RNA_def_property_ui_text(prop, "Clip Start", "Objects nearer than this are not visible to map.");

	prop= RNA_def_property(srna, "clip_end", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "clipend");
	RNA_def_property_range(prop, 0.01, FLT_MAX);
	RNA_def_property_ui_range(prop, 0.01, 50, 100, 2);
	RNA_def_property_ui_text(prop, "Clip Start", "Objects further than this are not visible to map.");

	prop= RNA_def_property(srna, "zoom", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "viewscale");
	RNA_def_property_range(prop, 0.01, FLT_MAX);
	RNA_def_property_ui_range(prop, 0.5, 5, 100, 2);
	RNA_def_property_ui_text(prop, "Zoom", "");

	/* XXX: EnvMap.notlay */
	
	prop= RNA_def_property(srna, "Resolution", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "cuberes");
	RNA_def_property_range(prop, 50, 4096);
	RNA_def_property_ui_text(prop, "Resolution", "Pixel resolution of the rendered environment map.");

	prop= RNA_def_property(srna, "depth", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 0, 5);
	RNA_def_property_ui_text(prop, "Depth", "Number of times a map will be rendered recursively (mirror effects.)");
}

void RNA_def_texture(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_type_items[] = {
		{TEX_CLOUDS, "CLOUDS", "Clouds", ""},
		{TEX_WOOD, "WOOD", "Wood", ""},
		{TEX_MARBLE, "MARBLE", "Marble", ""},
		{TEX_MAGIC, "MAGIC", "Magic", ""},
		{TEX_BLEND, "BLEND", "Blend", ""},
		{TEX_STUCCI, "STUCCI", "Stucci", ""},
		{TEX_NOISE, "NOISE", "Noise", ""},
		{TEX_IMAGE, "IMAGE", "Image", ""},
		{TEX_PLUGIN, "PLUGIN", "Plugin", ""},
		{TEX_ENVMAP, "ENVIRONMENT_MAP", "Environment Map", ""},
		{TEX_MUSGRAVE, "MUSGRAVE", "Musgrave", ""},
		{TEX_VORONOI, "VORONOI", "Voronoi", ""},
		{TEX_DISTNOISE, "DISTORTED_NOISE", "Distorted Noise", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_distance_metric_items[] = {
		{TEX_DISTANCE, "DISTANCE", "Actual Distance", ""},
		{TEX_DISTANCE_SQUARED, "DISTANCE_SQUARED", "Distance Squared", ""},
		{TEX_MANHATTAN, "MANHATTAN", "Manhattan", ""},
		{TEX_CHEBYCHEV, "CHEBYCHEV", "Chebychev", ""},
		{TEX_MINKOVSKY_HALF, "MINKOVSKY_HALF", "Minkovsky 1/2", ""},
		{TEX_MINKOVSKY_FOUR, "MINKOVSKY_FOUR", "Minkovsky 4", ""},
		{TEX_MINKOVSKY, "MINKOVSKY", "Minkovsky", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_color_type_items[] = {
		/* XXX: OK names / descriptions? */
		{TEX_INTENSITY, "INTENSITY", "Intensity", "Only calculate intensity."},
		{TEX_COL1, "POSITION", "Position", "Color cells by position."},
		{TEX_COL2, "POSITION_OUTLINE", "Position and Outline", "Use position plus an outline based on F2-F.1"},
		{TEX_COL3, "POSITION_OUTLINE_INTENSITY", "Position, Outline, and Intensity", "Multiply position and outline by intensity."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_noise_basis_items[] = {
		{TEX_BLENDER, "BLENDER_ORIGINAL", "Blender Original", ""},
		{TEX_STDPERLIN, "ORIGINAL_PERLIN", "Original Perlin", ""},
		{TEX_NEWPERLIN, "IMPROVED_PERLIN", "Improved Perlin", ""},
		{TEX_VORONOI_F1, "VORONOI_F1", "Voronoi F1", ""},
		{TEX_VORONOI_F2, "VORONOI_F2", "Voronoi F2", ""},
		{TEX_VORONOI_F3, "VORONOI_F3", "Voronoi F3", ""},
		{TEX_VORONOI_F4, "VORONOI_F4", "Voronoi F4", ""},
		{TEX_VORONOI_F2F1, "VORONOI_F2_F1", "Voronoi F2-F1", ""},
		{TEX_VORONOI_CRACKLE, "VORONOI_CRACKLE", "Voronoi Crackle", ""},
		{TEX_CELLNOISE, "CELL_NOISE", "Cell Noise", ""},
		{0, NULL, NULL, NULL}};

	rna_def_environment_map(brna);

	srna= RNA_def_struct(brna, "Texture", "ID");
	RNA_def_struct_sdna(srna, "Tex");
	RNA_def_struct_ui_text(srna, "Texture", "DOC_BROKEN");

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_type_items);
	RNA_def_property_ui_text(prop, "Type", "");

	prop= RNA_def_property(srna, "noise_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "noisesize");
	RNA_def_property_range(prop, 0.0001, FLT_MAX);
	RNA_def_property_ui_range(prop, 0.0001, 2, 10, 2);
	RNA_def_property_ui_text(prop, "Noise Size", "");

	prop= RNA_def_property(srna, "turbulance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "turbul");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 200, 10, 2);
	RNA_def_property_ui_text(prop, "Turbulance", "");

	prop= RNA_def_property(srna, "brightness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "bright");
	RNA_def_property_range(prop, 0, 2);
	RNA_def_property_ui_text(prop, "Brightness", "");

	prop= RNA_def_property(srna, "contrast", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.01, 5);
	RNA_def_property_ui_text(prop, "Contrast", "");

	/* XXX: would be nicer to have this as a color selector?
	   but the values can go past [0,1]. */
	prop= RNA_def_property(srna, "rgb_factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "rfac");
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, 0, 2);
	RNA_def_property_ui_text(prop, "RGB Factor", "");

	/* XXX: tex->filtersize */

	/* Musgrave */
	prop= RNA_def_property(srna, "highest_dimension", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mg_H");
	RNA_def_property_range(prop, 0.0001, 2);
	RNA_def_property_ui_text(prop, "Highest Dimension", "Highest fractal dimension for musgrave.");

	prop= RNA_def_property(srna, "lacunarity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mg_lacunarity");
	RNA_def_property_range(prop, 0, 6);
	RNA_def_property_ui_text(prop, "Lacunarity", "Gap between succesive frequencies for musgrave.");

	prop= RNA_def_property(srna, "octaves", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mg_octaves");
	RNA_def_property_range(prop, 0, 8);
	RNA_def_property_ui_text(prop, "Octaves", "Number of frequencies used for musgrave.");

	prop= RNA_def_property(srna, "offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mg_offset");
	RNA_def_property_range(prop, 0, 6);
	RNA_def_property_ui_text(prop, "Offset", "The fractal offset for musgrave.");

	prop= RNA_def_property(srna, "gain", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mg_gain");
	RNA_def_property_range(prop, 0, 6);
	RNA_def_property_ui_text(prop, "Gain", "The gain multiplier for musgrave.");

	/* Distorted Noise */
	prop= RNA_def_property(srna, "distortion_amount", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dist_amount");
	RNA_def_property_range(prop, 0, 10);
	RNA_def_property_ui_text(prop, "Distortion Amount", "");

	/* Musgrave / Voronoi */
	prop= RNA_def_property(srna, "noise_intensity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ns_outscale");
	RNA_def_property_range(prop, 0, 10);
	RNA_def_property_ui_text(prop, "Noise Intensity", "");

	/* Voronoi */
	prop= RNA_def_property(srna, "feature_weights", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "vn_w1");
	RNA_def_property_array(prop, 4);
	RNA_def_property_range(prop, -2, 2);
	RNA_def_property_ui_text(prop, "Feature Weights", "");

	prop= RNA_def_property(srna, "minkovsky_exponent", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "vn_mexp");
	RNA_def_property_range(prop, 0.01, 10);
	RNA_def_property_ui_text(prop, "Minkovsky Exponent", "");

	prop= RNA_def_property(srna, "distance_metric", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "vn_distm");
	RNA_def_property_enum_items(prop, prop_distance_metric_items);
	RNA_def_property_ui_text(prop, "Distance Metric", "");

	prop= RNA_def_property(srna, "color_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "vn_coltype");
	RNA_def_property_enum_items(prop, prop_color_type_items);
	RNA_def_property_ui_text(prop, "Color Type", "");

	prop= RNA_def_property(srna, "noise_basis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "noisebasis");
	RNA_def_property_enum_items(prop, prop_noise_basis_items);
	RNA_def_property_ui_text(prop, "Noise Basis", "");

	/* XXX: noisebasis2 */
	/* XXX: imaflag */
	/* XXX: flag */
	/* XXX: stype */

	/* XXX: did this as an array, but needs better descriptions than "1 2 3 4"
	        perhaps a new subtype could be added? */
	prop= RNA_def_property(srna, "crop_rectangle", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "cropxmin");
	RNA_def_property_array(prop, 4);
	RNA_def_property_range(prop, -10, 10);
	RNA_def_property_ui_text(prop, "Crop Rectangle", "");
	
	prop= RNA_def_property(srna, "checker_separation", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "checkerdist");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Checker Separation", "");
	
	prop= RNA_def_property(srna, "nabla", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.001, 0.1);
	RNA_def_property_ui_range(prop, 0.001, 0.1, 1, 2);
	RNA_def_property_ui_text(prop, "Nabla", "Size of derivative offset used for calculating normal.");

	prop= RNA_def_property(srna, "normal_factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "norfac");
	RNA_def_property_range(prop, 0, 25);
	RNA_def_property_ui_text(prop, "Normal Factor", "Amount the texture affects normal values.");

	rna_def_ipo_common(srna);
       
	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ima");
	RNA_def_property_struct_type(prop, "Image");
	RNA_def_property_ui_text(prop, "Image", "");

	/* XXX: plugin */

	/*
	prop= RNA_def_property(srna, "color_band", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "coba");
	RNA_def_property_struct_type(prop, "ColorBand");
	RNA_def_property_ui_text(prop, "Color Band", "");*/

	prop= RNA_def_property(srna, "environment_map", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "env");
	RNA_def_property_struct_type(prop, "EnvironmentMap");
	RNA_def_property_ui_text(prop, "Environment Map", "");

	/* XXX: preview */

}

#endif
