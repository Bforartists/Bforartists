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

#include "DNA_material_types.h"
#include "DNA_texture_types.h"
#include "DNA_world_types.h"

#ifdef RNA_RUNTIME

static PointerRNA rna_World_ambient_occlusion_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_WorldAmbientOcclusion, ptr->id.data);
}

static PointerRNA rna_World_stars_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_WorldStarsSettings, ptr->id.data);
}

static PointerRNA rna_World_mist_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_WorldMistSettings, ptr->id.data);
}

static void rna_World_mtex_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	World *wo= (World*)ptr->data;
	rna_iterator_array_begin(iter, (void*)wo->mtex, sizeof(MTex*), MAX_MTEX, NULL);
}

static PointerRNA rna_World_active_texture_get(PointerRNA *ptr)
{
	World *wo= (World*)ptr->data;

	return rna_pointer_inherit_refine(ptr, &RNA_TextureSlot, wo->mtex[(int)wo->texact]);
}

#else

static void rna_def_world_mtex(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem texco_items[] = {
		{TEXCO_VIEW, "VIEW", "View", "Uses view vector for the texture coordinates."},
		{TEXCO_GLOB, "GLOBAL", "Global", "Uses global coordinates for the texture coordinates (interior mist)."},
		{TEXCO_ANGMAP, "ANGMAP", "AngMap", "Uses 360 degree angular coordinates, e.g. for spherical light probes."},
		{TEXCO_H_SPHEREMAP, "SPHERE", "Sphere", "For 360 degree panorama sky, spherical mapped, only top half."},
		{TEXCO_H_TUBEMAP, "TUBE", "Tube", "For 360 degree panorama sky, cylindrical mapped, only top half."},
		{TEXCO_OBJECT, "OBJECT", "Object", "Uses linked object's coordinates for texture coordinates."},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "WorldTextureSlot", "TextureSlot");
	RNA_def_struct_sdna(srna, "MTex");
	RNA_def_struct_ui_text(srna, "World Texture Slot", "Texture slot for textures in a World datablock.");

	/* map to */
	prop= RNA_def_property(srna, "map_to_blend", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", WOMAP_BLEND);
	RNA_def_property_ui_text(prop, "Map To Blend", "Causes the texture to affect the color progression of the background.");

	prop= RNA_def_property(srna, "map_to_horizon", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", WOMAP_HORIZ);
	RNA_def_property_ui_text(prop, "Map To Horizon", "Causes the texture to affect the color of the horizon.");

	prop= RNA_def_property(srna, "map_to_zenith_up", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", WOMAP_ZENUP);
	RNA_def_property_ui_text(prop, "Map To Zenith Up", "Causes the texture to affect the color of the zenith above.");

	prop= RNA_def_property(srna, "map_to_zenith_down", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", WOMAP_ZENDOWN);
	RNA_def_property_ui_text(prop, "Map To Zenith Down", "Causes the texture to affect the color of the zenith below.");

	/* unused
	prop= RNA_def_property(srna, "map_to_mist", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", WOMAP_MIST);
	RNA_def_property_ui_text(prop, "Map To Mist", "Causes the texture to affect the intensity of the mist.");*/

	prop= RNA_def_property(srna, "texture_coordinates", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "texco");
	RNA_def_property_enum_items(prop, texco_items);
	RNA_def_property_ui_text(prop, "Texture Coordinates", "Textures coordinates used to map the texture with.");

	prop= RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Object", "Object to use for mapping with Object texture coordinates.");
}

static void rna_def_ambient_occlusion(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem blend_mode_items[] = {
		{WO_AOADD, "ADD", "Add", "Add light and shadow."},
		{WO_AOSUB, "SUBTRACT", "Subtract", "Subtract light and shadow (needs a normal light to make anything visible.)"},
		{WO_AOADDSUB, "BOTH", "Both", "Both lighten and darken."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_color_items[] = {
		{WO_AOPLAIN, "PLAIN", "White", "Plain diffuse energy (white.)"},
		{WO_AOSKYCOL, "SKY_COLOR", "Sky Color", "Use horizon and zenith color for diffuse energy."},
		{WO_AOSKYTEX, "SKY_TEXTURE", "Sky Texture", "Does full Sky texture render for diffuse energy."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_sample_method_items[] = {
		{WO_AOSAMP_CONSTANT, "CONSTANT_JITTERED", "Constant Jittered", ""},
		{WO_AOSAMP_HALTON, "ADAPTIVE_QMC", "Adaptive QMC", "Fast in high-contrast areas."},
		{WO_AOSAMP_HAMMERSLEY, "CONSTANT_QMC", "Constant QMC", "Best quality."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_gather_method_items[] = {
		{WO_AOGATHER_RAYTRACE, "RAYTRACE", "Raytrace", "Accurate, but slow when noise-free results are required."},
		{WO_AOGATHER_APPROX, "APPROXIMATE", "Approximate", "Inaccurate, but faster and without noise."},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "WorldAmbientOcclusion", NULL);
	RNA_def_struct_sdna(srna, "World");
	RNA_def_struct_nested(brna, srna, "World");
	RNA_def_struct_ui_text(srna, "Ambient Occlusion", "Ambient occlusion settings for a World datablock.");

	prop= RNA_def_property(srna, "enabled", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", WO_AMB_OCC);
	RNA_def_property_ui_text(prop, "Enabled", "");

	prop= RNA_def_property(srna, "distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "aodist");
	RNA_def_property_range(prop, 0.001, 5000);
	RNA_def_property_ui_text(prop, "Distance", "Length of rays, defines how far away other faces give occlusion effect.");

	prop= RNA_def_property(srna, "strength", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "aodistfac");
	RNA_def_property_range(prop, 0.00001, 10);
	RNA_def_property_ui_text(prop, "Strength", "Distance attenuation factor, the higher, the 'shorter' the shadows.");

	prop= RNA_def_property(srna, "energy", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "aoenergy");
	RNA_def_property_range(prop, 0.01, 3);
	RNA_def_property_ui_text(prop, "Energy", "Global energy scale for ambient occlusion.");

	prop= RNA_def_property(srna, "bias", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "aobias");
	RNA_def_property_range(prop, 0, 0.5);
	RNA_def_property_ui_text(prop, "Bias", "Bias (in radians) to prevent smoothed faces from showing banding (for Raytrace Constant Jittered).");

	prop= RNA_def_property(srna, "threshold", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ao_adapt_thresh");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Threshold", "Samples below this threshold will be considered fully shadowed/unshadowed and skipped (for Raytrace Adaptive QMC).");

	prop= RNA_def_property(srna, "adapt_to_speed", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ao_adapt_speed_fac");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Adapt To Speed", "Use the speed vector pass to reduce AO samples in fast moving pixels. Higher values result in more aggressive sample reduction. Requires Vec pass enabled (for Raytrace Adaptive QMC).");

	prop= RNA_def_property(srna, "error_tolerance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ao_approx_error");
	RNA_def_property_range(prop, 0.0001, 10);
	RNA_def_property_ui_text(prop, "Error Tolerance", "Low values are slower and higher quality (for Approximate).");

	prop= RNA_def_property(srna, "correction", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ao_approx_correction");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Correction", "Ad-hoc correction for over-occlusion due to the approximation (for Approximate).");

	prop= RNA_def_property(srna, "falloff", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "aomode", WO_AODIST);
	RNA_def_property_ui_text(prop, "Falloff", "");

	prop= RNA_def_property(srna, "pixel_cache", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "aomode", WO_AOCACHE);
	RNA_def_property_ui_text(prop, "Pixel Cache", "Cache AO results in pixels and interpolate over neighbouring pixels for speedup (for Approximate).");

	prop= RNA_def_property(srna, "samples", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "aosamp");
	RNA_def_property_range(prop, 1, 32);
	RNA_def_property_ui_text(prop, "Samples", "");

	prop= RNA_def_property(srna, "blend_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "aomix");
	RNA_def_property_enum_items(prop, blend_mode_items);
	RNA_def_property_ui_text(prop, "Blend Mode", "Blending mode for how AO mixes with material shading.");

	prop= RNA_def_property(srna, "color", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "aocolor");
	RNA_def_property_enum_items(prop, prop_color_items);
	RNA_def_property_ui_text(prop, "Color", "");

	prop= RNA_def_property(srna, "sample_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "ao_samp_method");
	RNA_def_property_enum_items(prop, prop_sample_method_items);
	RNA_def_property_ui_text(prop, "Sample Method", "Method for generating shadow samples (for Raytrace).");

	prop= RNA_def_property(srna, "gather_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "ao_gather_method");
	RNA_def_property_enum_items(prop, prop_gather_method_items);
	RNA_def_property_ui_text(prop, "Gather Method", "");

	prop= RNA_def_property(srna, "passes", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ao_approx_passes");
	RNA_def_property_range(prop, 0, 10);
	RNA_def_property_ui_text(prop, "Passes", "Number of preprocessing passes to reduce overocclusion (for Approximate).");
}

static void rna_def_world_mist(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem falloff_items[] = {
		{0, "QUADRATIC", "Quadratic", "Mist uses quadratic progression."},
		{1, "LINEAR", "Linear", "Mist uses linear progression."},
		{2, "INVERSE_QUADRATIC", "Inverse Quadratic", "Mist uses inverse quadratic progression."},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "WorldMistSettings", NULL);
	RNA_def_struct_sdna(srna, "World");
	RNA_def_struct_nested(brna, srna, "World");
	RNA_def_struct_ui_text(srna, "World Mist", "Mist settings for a World data-block.");

	prop= RNA_def_property(srna, "enabled", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", WO_MIST);
	RNA_def_property_ui_text(prop, "Enabled", "Enable mist, occluding objects with the environment color as they are further away.");

	prop= RNA_def_property(srna, "intensity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "misi");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Intensity", "Intensity of the mist.");

	prop= RNA_def_property(srna, "start", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "miststa");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 10000, 10, 2);
	RNA_def_property_ui_text(prop, "Start", "Starting distance of the mist.");

	prop= RNA_def_property(srna, "depth", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mistdist");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 10000, 10, 2);
	RNA_def_property_ui_text(prop, "Depth", "Depth of the mist.");

	prop= RNA_def_property(srna, "height", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "misthi");
	RNA_def_property_range(prop, 0, 100);
	RNA_def_property_ui_text(prop, "Height", "Factor for a less dense mist with increasing height.");
	
	prop= RNA_def_property(srna, "falloff", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mistype");
	RNA_def_property_enum_items(prop, falloff_items);
	RNA_def_property_ui_text(prop, "Falloff", "Falloff method for mist.");
}

static void rna_def_world_stars(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "WorldStarsSettings", NULL);
	RNA_def_struct_sdna(srna, "World");
	RNA_def_struct_nested(brna, srna, "World");
	RNA_def_struct_ui_text(srna, "World Stars", "Stars setting for a World data-block.");

	prop= RNA_def_property(srna, "enabled", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", WO_STARS);
	RNA_def_property_ui_text(prop, "Enabled", "Enable starfield generation.");

	prop= RNA_def_property(srna, "size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "starsize");
	RNA_def_property_range(prop, 0, 10);
	RNA_def_property_ui_text(prop, "Size", "Average screen dimension of stars.");

	prop= RNA_def_property(srna, "min_distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "starmindist");
	RNA_def_property_range(prop, 0, 1000);
	RNA_def_property_ui_text(prop, "Minimum Distance", "Minimum distance to the camera for stars.");

	prop= RNA_def_property(srna, "average_separation", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "stardist");
	RNA_def_property_range(prop, 2, 1000);
	RNA_def_property_ui_text(prop, "Average Separation", "Average distance between any two stars.");

	prop= RNA_def_property(srna, "color_randomization", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "starcolnoise");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Color Randomization", "Randomizes star color.");
	
	/* unused
	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "starr");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Color", "Stars color.");*/
}

void RNA_def_world(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem physics_engine_items[] = {
		{WOPHY_NONE, "NONE", "None", ""},
		//{WOPHY_ENJI, "ENJI", "Enji", ""},
		{WOPHY_SUMO, "SUMO", "Sumo (Deprecated)", ""},
		//{WOPHY_DYNAMO, "DYNAMO", "Dynamo", ""},
		//{WOPHY_ODE, "ODE", "ODE", ""},
		{WOPHY_BULLET, "BULLET", "Bullet", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "World", "ID");
	RNA_def_struct_ui_text(srna, "World", "World datablock describing the environment and ambient lighting of a scene.");

	rna_def_animdata_common(srna);
	rna_def_mtex_common(srna, "rna_World_mtex_begin", "rna_World_active_texture_get", "WorldTextureSlot");

	/* colors */
	prop= RNA_def_property(srna, "horizon_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "horr");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Horizon Color", "Color at the horizon.");

	prop= RNA_def_property(srna, "zenith_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "zenr");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Zenith Color", "Color at the zenith.");

	prop= RNA_def_property(srna, "ambient_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "ambr");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Ambient Color", "");

	/* exp, range */
	prop= RNA_def_property(srna, "exposure", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "exp");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Exposure", "Amount of exponential color correction for light.");

	prop= RNA_def_property(srna, "range", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "range");
	RNA_def_property_range(prop, 0.2, 5.0);
	RNA_def_property_ui_text(prop, "Range", "The color amount that will be mapped on color 1.0.");

	/* sky type */
	prop= RNA_def_property(srna, "blend_sky", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "skytype", WO_SKYBLEND);
	RNA_def_property_ui_text(prop, "Blend Sky", "Renders background with natural progression from horizon to zenith.");

	prop= RNA_def_property(srna, "paper_sky", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "skytype", WO_SKYPAPER);
	RNA_def_property_ui_text(prop, "Paper Sky", "Flattens blend or texture coordinates.");

	prop= RNA_def_property(srna, "real_sky", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "skytype", WO_SKYREAL);
	RNA_def_property_ui_text(prop, "Real Sky", "Renders background with a real horizon.");

	/* physics */
	prop= RNA_def_property(srna, "physics_engine", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "physicsEngine");
	RNA_def_property_enum_items(prop, physics_engine_items);
	RNA_def_property_ui_text(prop, "Physics Engine", "Physics engine used for physics simulation in the game engine.");

	prop= RNA_def_property(srna, "physics_gravity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "gravity");
	RNA_def_property_range(prop, 0.0, 25.0);
	RNA_def_property_ui_text(prop, "Physics Gravity", "Gravitational constant used for physics simulation in the game engine.");

	/* nested structs */
	prop= RNA_def_property(srna, "ambient_occlusion", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "WorldAmbientOcclusion");
	RNA_def_property_pointer_funcs(prop, "rna_World_ambient_occlusion_get", NULL);
	RNA_def_property_ui_text(prop, "Ambient Occlusion", "World ambient occlusion settings.");

	prop= RNA_def_property(srna, "mist", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "WorldMistSettings");
	RNA_def_property_pointer_funcs(prop, "rna_World_mist_get", NULL);
	RNA_def_property_ui_text(prop, "Mist", "World mist settings.");

	prop= RNA_def_property(srna, "stars", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "WorldStarsSettings");
	RNA_def_property_pointer_funcs(prop, "rna_World_stars_get", NULL);
	RNA_def_property_ui_text(prop, "Stars", "World stars settings.");

	prop= RNA_def_property(srna, "script_link", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "scriptlink");
	RNA_def_property_ui_text(prop, "Script Link", "Scripts linked to this object.");

	rna_def_ambient_occlusion(brna);
	rna_def_world_mist(brna);
	rna_def_world_stars(brna);
	rna_def_world_mtex(brna);
}

#endif

