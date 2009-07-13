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

#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_texture_types.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

static void rna_Lamp_buffer_size_set(PointerRNA *ptr, int value)
{
	Lamp *la= (Lamp*)ptr->data;

	CLAMP(value, 512, 10240);
	la->bufsize= value;
	la->bufsize &= (~15); /* round to multiple of 16 */
}

static PointerRNA rna_Lamp_sky_settings_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_LampSkySettings, ptr->id.data);
}

static void rna_Lamp_mtex_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Lamp *la= (Lamp*)ptr->data;
	rna_iterator_array_begin(iter, (void*)la->mtex, sizeof(MTex*), MAX_MTEX, 0, NULL);
}

static PointerRNA rna_Lamp_active_texture_get(PointerRNA *ptr)
{
	Lamp *la= (Lamp*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_TextureSlot, la->mtex[(int)la->texact]);
}

static StructRNA* rna_Lamp_refine(struct PointerRNA *ptr)
{
	Lamp *la= (Lamp*)ptr->data;

	switch(la->type) {
		case LA_LOCAL:
			return &RNA_LocalLamp;
		case LA_SUN:
			return &RNA_SunLamp;
		case LA_SPOT:
			return &RNA_SpotLamp;
		case LA_HEMI:
			return &RNA_HemiLamp;
		case LA_AREA:
			return &RNA_AreaLamp;
		default:
			return &RNA_Lamp;
	}
}

#else

static void rna_def_lamp_mtex(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_texture_coordinates_items[] = {
		{TEXCO_GLOB, "GLOBAL", 0, "Global", "Uses global coordinates for the texture coordinates."},
		{TEXCO_VIEW, "VIEW", 0, "View", "Uses view coordinates for the texture coordinates."},
		{TEXCO_OBJECT, "OBJECT", 0, "Object", "Uses linked object's coordinates for texture coordinates."},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "LampTextureSlot", "TextureSlot");
	RNA_def_struct_sdna(srna, "MTex");
	RNA_def_struct_ui_text(srna, "Lamp Texture Slot", "Texture slot for textures in a Lamp datablock.");

	prop= RNA_def_property(srna, "texture_coordinates", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "texco");
	RNA_def_property_enum_items(prop, prop_texture_coordinates_items);
	RNA_def_property_ui_text(prop, "Texture Coordinates", "");

	prop= RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Object", "Object to use for mapping with Object texture coordinates.");

	prop= RNA_def_property(srna, "map_to_color", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", LAMAP_COL);
	RNA_def_property_ui_text(prop, "Map To Color", "Lets the texture affect the basic color of the lamp.");

	prop= RNA_def_property(srna, "map_to_shadow", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mapto", LAMAP_SHAD);
	RNA_def_property_ui_text(prop, "Map To Shadow", "Lets the texture affect the shadow color of the lamp.");
}

static void rna_def_lamp_sky_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_skycolorspace_items[] = {
		{0, "SMPTE", 0, "SMPTE", ""},
		{1, "REC709", 0, "REC709", ""},
		{2, "CIE", 0, "CIE", ""},
		{0, NULL, 0, NULL, NULL}};
		
	static EnumPropertyItem prop_blendmode_items[] = {
		{0, "MIX", 0, "Mix", ""},
		{1, "ADD", 0, "Add", ""},
		{2, "MULTIPLY", 0, "Multiply", ""},
		{3, "SUBTRACT", 0, "Subtract", ""},
		{4, "SCREEN", 0, "Screen", ""},
		{5, "DIVIDE", 0, "Divide", ""},
		{6, "DIFFERENCE", 0, "Difference", ""},
		{7, "DARKEN", 0, "Darken", ""},
		{8, "LIGHTEN", 0, "Lighten", ""},
		{9, "OVERLAY", 0, "Overlay", ""},
		{10, "DODGE", 0, "Dodge", ""},
		{11, "BURN", 0, "Burn", ""},
		{12, "HUE", 0, "Hue", ""},
		{13, "SATURATION", 0, "Saturation", ""},
		{14, "VALUE", 0, "Value", ""},
		{15, "COLOR", 0, "Color", ""},
		{0, NULL, 0, NULL, NULL}};
		
	srna= RNA_def_struct(brna, "LampSkySettings", NULL);
	RNA_def_struct_sdna(srna, "Lamp");
	RNA_def_struct_nested(brna, srna, "SunLamp");
	RNA_def_struct_ui_text(srna, "Lamp Sky Settings", "Sky related settings for a sun lamp.");
		
	prop= RNA_def_property(srna, "sky_color_space", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "sky_colorspace");
	RNA_def_property_enum_items(prop, prop_skycolorspace_items);
	RNA_def_property_ui_text(prop, "Sky Color Space", "Color space to use for internal XYZ->RGB color conversion.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "sky_blend_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "skyblendtype");
	RNA_def_property_enum_items(prop, prop_blendmode_items);
	RNA_def_property_ui_text(prop, "Sky Blend Mode", "Blend mode for combining sun sky with world sky.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);
	
	/* Number values */
	
	prop= RNA_def_property(srna, "horizon_brightness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 20.0f);
	RNA_def_property_ui_text(prop, "Horizon Brightness", "Horizon brightness.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "spread", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Horizon Spread", "Horizon Spread.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "sun_brightness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Sun Brightness", "Sun brightness.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "sun_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Sun Size", "Sun size.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

  	prop= RNA_def_property(srna, "backscattered_light", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, -1.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Backscattered Light", "Backscattered light.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "sun_intensity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Sun Intensity", "Sun intensity.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "atmosphere_turbidity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "atm_turbidity");
	RNA_def_property_range(prop, 1.0f, 30.0f);
	RNA_def_property_ui_text(prop, "Atmosphere Turbidity", "Sky turbidity.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "atmosphere_inscattering", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "atm_inscattering_factor");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Atmosphere Inscatter", "Scatter contribution factor.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "atmosphere_extinction", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "atm_extinction_factor");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Atmosphere Extinction", "Extinction scattering contribution factor.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "atmosphere_distance_factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "atm_distance_factor");
	RNA_def_property_range(prop, 0.0f, 500.0f);
	RNA_def_property_ui_text(prop, "Atmosphere Distance Factor", "Multiplier to convert blender units to physical distance.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "sky_blend", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "skyblendfac");
	RNA_def_property_range(prop, 0.0f, 2.0f);
	RNA_def_property_ui_text(prop, "Sky Blend", "Blend factor with sky.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "sky_exposure", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 20.0f);
	RNA_def_property_ui_text(prop, "Sky Exposure", "Strength of sky shading exponential exposure correction.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	/* boolean */
	
	prop= RNA_def_property(srna, "sky", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "sun_effect_type", LA_SUN_EFFECT_SKY);
	RNA_def_property_ui_text(prop, "Sky", "Apply sun effect on sky.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);

	prop= RNA_def_property(srna, "atmosphere", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "sun_effect_type", LA_SUN_EFFECT_AP);
	RNA_def_property_ui_text(prop, "Atmosphere", "Apply sun effect on atmosphere.");
	RNA_def_property_update(prop, NC_LAMP|ND_SKY, NULL);
}

static void rna_def_lamp(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_type_items[] = {
		{LA_LOCAL, "POINT", ICON_LAMP_POINT, "Point", "Omnidirectional point light source."},
		{LA_SUN, "SUN", ICON_LAMP_SUN, "Sun", "Constant direction parallel ray light source."},
		{LA_SPOT, "SPOT", ICON_LAMP_SPOT, "Spot", "Directional cone light source."},
		{LA_HEMI, "HEMI", ICON_LAMP_HEMI, "Hemi", "180 degree constant light source."},
		{LA_AREA, "AREA", ICON_LAMP_AREA, "Area", "Directional area light source."},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "Lamp", "ID");
	RNA_def_struct_refine_func(srna, "rna_Lamp_refine");
	RNA_def_struct_ui_text(srna, "Lamp", "Lamp datablock for lighting a scene.");
	RNA_def_struct_ui_icon(srna, ICON_LAMP_DATA);

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_type_items);
	RNA_def_property_ui_text(prop, "Type", "Type of Lamp.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dist");
	RNA_def_property_ui_range(prop, 0, 1000, 1.0, 2);
	RNA_def_property_ui_text(prop, "Distance", "Falloff distance - the light is at half the original intensity at this point.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "energy", PROP_FLOAT, PROP_NONE);
	RNA_def_property_ui_range(prop, 0, 10.0, 0.1, 2);
	RNA_def_property_ui_text(prop, "Energy", "Amount of light that the lamp emits.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "r");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Color", "Light color.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_LAYER);
	RNA_def_property_ui_text(prop, "Layer", "Illuminates objects only on the same layer the lamp is on.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "negative", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_NEG);
	RNA_def_property_ui_text(prop, "Negative", "Lamp casts negative light.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "specular", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "mode", LA_NO_SPEC);
	RNA_def_property_ui_text(prop, "Specular", "Lamp creates specular highlights.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "diffuse", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "mode", LA_NO_DIFF);
	RNA_def_property_ui_text(prop, "Diffuse", "Lamp does diffuse shading.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	/* textures */
	rna_def_mtex_common(srna, "rna_Lamp_mtex_begin", "rna_Lamp_active_texture_get", "LampTextureSlot");

	/* script link */
	prop= RNA_def_property(srna, "script_link", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "scriptlink");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Script Link", "Scripts linked to this lamp.");
}

static void rna_def_lamp_falloff(StructRNA *srna)
{
	PropertyRNA *prop;

	static EnumPropertyItem prop_fallofftype_items[] = {
		{LA_FALLOFF_CONSTANT, "CONSTANT", 0, "Constant", ""},
		{LA_FALLOFF_INVLINEAR, "INVERSE_LINEAR", 0, "Inverse Linear", ""},
		{LA_FALLOFF_INVSQUARE, "INVERSE_SQUARE", 0, "Inverse Square", ""},
		{LA_FALLOFF_CURVE, "CUSTOM_CURVE", 0, "Custom Curve", ""},
		{LA_FALLOFF_SLIDERS, "LINEAR_QUADRATIC_WEIGHTED", 0, "Lin/Quad Weighted", ""},
		{0, NULL, 0, NULL, NULL}};

	prop= RNA_def_property(srna, "falloff_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_fallofftype_items);
	RNA_def_property_ui_text(prop, "Falloff Type", "Intensity Decay with distance.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);
	
	prop= RNA_def_property(srna, "falloff_curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "curfalloff");
	RNA_def_property_ui_text(prop, "Falloff Curve", "Custom Lamp Falloff Curve");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "sphere", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_SPHERE);
	RNA_def_property_ui_text(prop, "Sphere", "Sets light intensity to zero beyond lamp distance.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "linear_attenuation", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "att1");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Linear Attenuation", "Linear distance attentuation.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "quadratic_attenuation", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "att2");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Quadratic Attenuation", "Quadratic distance attentuation.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);
}

static void rna_def_lamp_shadow(StructRNA *srna, int spot, int area)
{
	PropertyRNA *prop;

	static EnumPropertyItem prop_shadow_items[] = {
		{0, "NOSHADOW", 0, "No Shadow", ""},
		{LA_SHAD_RAY, "RAY_SHADOW", 0, "Ray Shadow", "Use ray tracing for shadow."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem prop_spot_shadow_items[] = {
		{0, "NOSHADOW", 0, "No Shadow", ""},
		{LA_SHAD_BUF, "BUFFER_SHADOW", 0, "Buffer Shadow", "Lets spotlight produce shadows using shadow buffer."},
		{LA_SHAD_RAY, "RAY_SHADOW", 0, "Ray Shadow", "Use ray tracing for shadow."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem prop_ray_sampling_method_items[] = {
		{LA_SAMP_HALTON, "ADAPTIVE_QMC", 0, "Adaptive QMC", ""},
		{LA_SAMP_HAMMERSLEY, "CONSTANT_QMC", 0, "Constant QMC", ""},
		{0, NULL, 0, NULL, NULL}};
	
	static EnumPropertyItem prop_spot_ray_sampling_method_items[] = {
		{LA_SAMP_HALTON, "ADAPTIVE_QMC", 0, "Adaptive QMC", ""},
		{LA_SAMP_HAMMERSLEY, "CONSTANT_QMC", 0, "Constant QMC", ""},
		{LA_SAMP_CONSTANT, "CONSTANT_JITTERED", 0, "Constant Jittered", ""},
		{0, NULL, 0, NULL, NULL}};


	prop= RNA_def_property(srna, "shadow_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, (spot)? prop_spot_shadow_items: prop_shadow_items);
	RNA_def_property_ui_text(prop, "Shadow Method", "Method to compute lamp shadow with.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shdwr");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Shadow Color", "Color of shadows casted by the lamp.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "only_shadow", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_ONLYSHADOW);
	RNA_def_property_ui_text(prop, "Only Shadow", "Causes light to cast shadows only without illuminating objects.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_ray_sampling_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "ray_samp_method");
	RNA_def_property_enum_items(prop, (area)? prop_spot_ray_sampling_method_items: prop_ray_sampling_method_items);
	RNA_def_property_ui_text(prop, "Shadow Ray Sampling Method", "Method for generating shadow samples: Adaptive QMC is fastest, Constant QMC is less noisy but slower.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, (area)? "shadow_ray_samples_x": "shadow_ray_samples", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ray_samp");
	RNA_def_property_range(prop, 1, 64);
	RNA_def_property_ui_text(prop, (area)? "Shadow Ray Samples": "Shadow Ray Samples X","Amount of samples taken extra (samples x samples).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	if(area) {
		prop= RNA_def_property(srna, "shadow_ray_samples_y", PROP_INT, PROP_NONE);
		RNA_def_property_int_sdna(prop, NULL, "ray_sampy");
		RNA_def_property_range(prop, 1, 64);
		RNA_def_property_ui_text(prop, "Shadow Ray Samples Y", "Amount of samples taken extra (samples x samples).");
		RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);
	}

	prop= RNA_def_property(srna, "shadow_adaptive_threshold", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "adapt_thresh");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Shadow Adaptive Threshold", "Threshold for Adaptive Sampling (Raytraced shadows).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_soft_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "soft");
	RNA_def_property_ui_range(prop, 0, 100, 0.1, 3);
	RNA_def_property_ui_text(prop, "Shadow Soft Size", "Light size for ray shadow sampling (Raytraced shadows).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_LAYER_SHADOW);
	RNA_def_property_ui_text(prop, "Shadow Layer", "Causes only objects on the same layer to cast shadows.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);
}

static void rna_def_local_lamp(BlenderRNA *brna)
{
	StructRNA *srna;

	srna= RNA_def_struct(brna, "LocalLamp", "Lamp");
	RNA_def_struct_sdna(srna, "Lamp");
	RNA_def_struct_ui_text(srna, "Local Lamp", "Omnidirectional point lamp.");

	rna_def_lamp_falloff(srna);
	rna_def_lamp_shadow(srna, 0, 0);
}

static void rna_def_area_lamp(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_areashape_items[] = {
		{LA_AREA_SQUARE, "SQUARE", 0, "Square", ""},
		{LA_AREA_RECT, "RECTANGLE", 0, "Rectangle", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "AreaLamp", "Lamp");
	RNA_def_struct_sdna(srna, "Lamp");
	RNA_def_struct_ui_text(srna, "Area Lamp", "Directional area lamp.");

	rna_def_lamp_shadow(srna, 0, 1);

	prop= RNA_def_property(srna, "umbra", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ray_samp_type", LA_SAMP_UMBRA);
	RNA_def_property_ui_text(prop, "Umbra", "Emphasize parts that are fully shadowed (Constant Jittered sampling).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "dither", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ray_samp_type", LA_SAMP_DITHER);
	RNA_def_property_ui_text(prop, "Dither", "Use 2x2 dithering for sampling  (Constant Jittered sampling).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "jitter", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ray_samp_type", LA_SAMP_JITTER);
	RNA_def_property_ui_text(prop, "Jitter", "Use noise for sampling  (Constant Jittered sampling).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shape", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "area_shape");
	RNA_def_property_enum_items(prop, prop_areashape_items);
	RNA_def_property_ui_text(prop, "Shape", "Shape of the area lamp.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "area_size");
	RNA_def_property_ui_range(prop, 0, 100, 0.1, 3);
	RNA_def_property_ui_text(prop, "Size", "Size of the area of the area Lamp, X direction size for Rectangle shapes.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "size_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "area_sizey");
	RNA_def_property_ui_range(prop, 0, 100, 0.1, 3);
	RNA_def_property_ui_text(prop, "Size Y", "Size of the area of the area Lamp in the Y direction for Rectangle shapes.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "gamma", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "k");
	RNA_def_property_ui_range(prop, 0.001, 2.0, 0.1, 3);
	RNA_def_property_ui_text(prop, "Gamma", "Light gamma correction value.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);
}

static void rna_def_spot_lamp(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_shadbuftype_items[] = {
		{LA_SHADBUF_REGULAR	, "REGULAR", 0, "Classical", "Classic shadow buffer."},
		{LA_SHADBUF_HALFWAY, "HALFWAY", 0, "Classic-Halfway", "Regular buffer, averaging the closest and 2nd closest Z value to reducing bias artifaces."},
		{LA_SHADBUF_IRREGULAR, "IRREGULAR", 0, "Irregular", "Irregular buffer produces sharp shadow always, but it doesn't show up for raytracing."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem prop_shadbuffiltertype_items[] = {
		{LA_SHADBUF_BOX	, "BOX", 0, "Box", "Apply the Box filter to shadow buffer samples."},
		{LA_SHADBUF_TENT, "TENT", 0, "Tent", "Apply the Tent Filter to shadow buffer samples."},
		{LA_SHADBUF_GAUSS, "GAUSS", 0, "Gauss", "Apply the Gauss filter to shadow buffer samples."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem prop_numbuffer_items[] = {
		{1, "BUFFERS_1", 0, "1", "Only one buffer rendered."},
		{4, "BUFFERS_4", 0, "4", "Renders 4 buffers for better AA, this quadruples memory usage."},
		{9, "BUFFERS_9", 0, "9", "Renders 9 buffers for better AA, this uses nine times more memory."},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "SpotLamp", "Lamp");
	RNA_def_struct_sdna(srna, "Lamp");
	RNA_def_struct_ui_text(srna, "Spot Lamp", "Directional cone lamp.");

	rna_def_lamp_falloff(srna);
	rna_def_lamp_shadow(srna, 1, 0);

	prop= RNA_def_property(srna, "square", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_SQUARE);
	RNA_def_property_ui_text(prop, "Square", "Casts a square spot light shape.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "halo", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", LA_HALO);
	RNA_def_property_ui_text(prop, "Halo", "Renders spotlight with a volumetric halo (Buffer Shadows).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "halo_intensity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "haint");
	RNA_def_property_ui_range(prop, 0, 5.0, 0.1, 3);
	RNA_def_property_ui_text(prop, "Halo Intensity", "Brightness of the spotlight's halo cone  (Buffer Shadows).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "halo_step", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "shadhalostep");
	RNA_def_property_range(prop, 0, 12);
	RNA_def_property_ui_text(prop, "Halo Step", "Volumetric halo sampling frequency.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "bufsize");
	RNA_def_property_range(prop, 512, 10240);
	RNA_def_property_ui_text(prop, "Shadow Buffer Size", "Resolution of the shadow buffer, higher values give crisper shadows but use more memory");
	RNA_def_property_int_funcs(prop, NULL, "rna_Lamp_buffer_size_set", NULL);
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_filter_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "filtertype");
	RNA_def_property_enum_items(prop, prop_shadbuffiltertype_items);
	RNA_def_property_ui_text(prop, "Shadow Filter Type", "Type of shadow filter (Buffer Shadows).");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_sample_buffers", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "buffers");
	RNA_def_property_enum_items(prop, prop_numbuffer_items);
	RNA_def_property_ui_text(prop, "Shadow Sample Buffers", "Number of shadow buffers to render for better AA, this increases memory usage.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "spot_blend", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "spotblend");
	RNA_def_property_range(prop, 0.0f ,1.0f);
	RNA_def_property_ui_text(prop, "Spot Blend", "The softness of the spotlight edge.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "spot_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "spotsize");
	RNA_def_property_range(prop, 1.0f ,180.0f);
	RNA_def_property_ui_text(prop, "Spot Size", "Angle of the spotlight beam in degrees.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_clip_start", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "clipsta");
	RNA_def_property_range(prop, 0.0f, 9999.0f);
	RNA_def_property_ui_text(prop, "Shadow Buffer Clip Start", "Shadow map clip start: objects closer will not generate shadows");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_clip_end", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "clipend");
	RNA_def_property_range(prop, 0.0f, 9999.0f);
	RNA_def_property_ui_text(prop, "Shadow Buffer Clip End", "Shadow map clip end beyond which objects will not generate shadows.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_bias", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "bias");
	RNA_def_property_range(prop, 0.0f, 5.0f);
	RNA_def_property_ui_text(prop, "Shadow Buffer Bias", "Shadow buffer sampling bias.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_soft", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "soft");
	RNA_def_property_range(prop, 0.0f, 100.0f);
	RNA_def_property_ui_text(prop, "Shadow Buffer Soft", "Size of shadow buffer sampling area.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_samples", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "samp");
	RNA_def_property_range(prop, 1, 16);
	RNA_def_property_ui_text(prop, "Samples", "Number of shadow buffer samples.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "shadow_buffer_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "buftype");
	RNA_def_property_enum_items(prop, prop_shadbuftype_items);
	RNA_def_property_ui_text(prop, "Shadow Buffer Type", "Type of shadow buffer.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING, NULL);

	prop= RNA_def_property(srna, "auto_clip_start", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "bufflag", LA_SHADBUF_AUTO_START);
	RNA_def_property_ui_text(prop, "Autoclip Start",  "Automatic calculation of clipping-start, based on visible vertices.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);

	prop= RNA_def_property(srna, "auto_clip_end", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "bufflag", LA_SHADBUF_AUTO_END);
	RNA_def_property_ui_text(prop, "Autoclip End", "Automatic calculation of clipping-end, based on visible vertices.");
	RNA_def_property_update(prop, NC_LAMP|ND_LIGHTING_DRAW, NULL);
}

static void rna_def_sun_lamp(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "SunLamp", "Lamp");
	RNA_def_struct_sdna(srna, "Lamp");
	RNA_def_struct_ui_text(srna, "Sun Lamp", "Constant direction parallel ray lamp.");

	rna_def_lamp_shadow(srna, 0, 0);

	/* sky */
	prop= RNA_def_property(srna, "sky", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "LampSkySettings");
	RNA_def_property_pointer_funcs(prop, "rna_Lamp_sky_settings_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Sky Settings", "Sky related settings for sun lamps.");

	rna_def_lamp_sky_settings(brna);
}

static void rna_def_hemi_lamp(BlenderRNA *brna)
{
	StructRNA *srna;

	srna= RNA_def_struct(brna, "HemiLamp", "Lamp");
	RNA_def_struct_sdna(srna, "Lamp");
	RNA_def_struct_ui_text(srna, "Hemi Lamp", "180 degree constant lamp.");
}

void RNA_def_lamp(BlenderRNA *brna)
{
	rna_def_lamp(brna);
	rna_def_local_lamp(brna);
	rna_def_area_lamp(brna);
	rna_def_spot_lamp(brna);
	rna_def_sun_lamp(brna);
	rna_def_hemi_lamp(brna);
	rna_def_lamp_mtex(brna);
}

#endif

