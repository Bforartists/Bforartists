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
 * Contributor(s): Blender Foundation (2008), Nathan Letwory, Robin Allen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_node_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "BKE_node.h"
#include "BKE_image.h"

#ifdef RNA_RUNTIME

StructRNA *rna_Node_refine(struct PointerRNA *ptr)
{
	bNode *node = (bNode*)ptr->data;

	switch(node->type) {
		
		#define DefNode(Category, ID, DefFunc, EnumName, StructName, UIName, UIDesc) \
			case ID: return &RNA_##Category##StructName;
				
		#include "rna_nodetree_types.h"
		
		#undef DefNode
		
		default:
			return &RNA_Node;
	}
}

#else

#define MaxNodes 1000

enum
{
	Category_NoCategory,
	Category_ShaderNode,
	Category_CompositorNode,
	Category_TextureNode
};

typedef struct NodeInfo
{
	int defined;
	int category;
	const char *enum_name;
	const char *struct_name;
	const char *base_name;
	int icon;
	const char *ui_name;
	const char *ui_desc;
} NodeInfo;

static NodeInfo nodes[MaxNodes];

static void reg_node(
	int ID, 
	int category,
	const char *enum_name,
	const char *struct_name,
	const char *base_name,
	const char *ui_name,
	const char *ui_desc
){
	NodeInfo *ni = nodes + ID;
	
	ni->defined = 1;
	ni->category = category;
	ni->enum_name = enum_name;
	ni->struct_name = struct_name;
	ni->base_name = base_name;
	ni->ui_name = ui_name;
	ni->ui_desc = ui_desc;
}

static void init(void)
{
	memset(nodes, 0, sizeof nodes);
	
	#define Str(x) #x
	
	#define DefNode(Category, ID, DefFunc, EnumName, StructName, UIName, UIDesc) \
		reg_node(ID, Category_##Category, EnumName, Str(Category##StructName), #Category, UIName, UIDesc);
		
	#include "rna_nodetree_types.h"
	
	#undef DefNode
	#undef Str
}

static StructRNA* def_node(BlenderRNA *brna, int node_id)
{
	StructRNA *srna;
	NodeInfo *node = nodes + node_id;
	
	srna = RNA_def_struct(brna, node->struct_name, node->base_name);
	RNA_def_struct_ui_text(srna, node->ui_name, node->ui_desc);
	RNA_def_struct_sdna(srna, "bNode");
	
	return srna;
}

static EnumPropertyItem* alloc_node_type_items(int category)
{
	int i;
	int count = 2;
	EnumPropertyItem *item, *items;
	
	for(i=0; i<MaxNodes; i++)
		if(nodes[i].defined && nodes[i].category == category)
			count++;
		
	item = items = malloc(count * sizeof(EnumPropertyItem));
	
	for(i=0; i<MaxNodes; i++) {
		NodeInfo *node = nodes + i;
		if(node->defined && node->category == category) {
			item->value = i;
			item->identifier = node->enum_name;
			item->icon = node->icon;
			item->name = node->ui_name;
			item->description = node->ui_desc;
		
			item++;
		}
	}
	
	item->value = NODE_DYNAMIC;
	item->identifier = "SCRIPT";
	item->name = "Script";
	item->description = "";
	
	item++;
	
	memset(item, 0, sizeof(EnumPropertyItem));
	
	return items;
}


/* -- Common nodes ---------------------------------------------------------- */

static void def_math(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem items[] = {
		{ 0, "ADD",          0, "Add",          ""},
		{ 1, "SUBTRACT",     0, "Subtract",     ""},
		{ 2, "MULTIPLY",     0, "Multiply",     ""},
		{ 3, "DIVIDE",       0, "Divide",       ""},
		{ 4, "SINE",         0, "Sine",         ""},
		{ 5, "COSINE",       0, "Cosine",       ""},
		{ 6, "TANGENT",      0, "Tangent",      ""},
		{ 7, "ARCSINE",      0, "Arcsine",      ""},
		{ 8, "ARCCOSINE",    0, "Arccosine",    ""},
		{ 9, "ARCTANGENT",   0, "Arctangent",   ""},
		{10, "POWER",        0, "Power",        ""},
		{11, "LOGARITHM",    0, "Logarithm",    ""},
		{12, "MINIMUM",      0, "Minimum",      ""},
		{13, "MAXIMUM",      0, "Maximum",      ""},
		{14, "ROUND",        0, "Round",        ""},
		{15, "LESS_THAN",    0, "Less Than",    ""},
		{16, "GREATER_THAN", 0, "Greater Than", ""},
		
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "operation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, items);
	RNA_def_property_ui_text(prop, "Operation", "");
}

static void def_vector_math(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem items[] = {
		{0, "ADD",           0, "Add",           ""},
		{1, "SUBTRACT",      0, "Subtract",      ""},
		{2, "AVERAGE",       0, "Average",       ""},
		{3, "DOT_PRODUCT",   0, "Dot Product",   ""},
		{4, "CROSS_PRODUCT", 0, "Cross Product", ""},
		{5, "NORMALIZE",     0, "Normalize",     ""},
		
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "operation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, items);
	RNA_def_property_ui_text(prop, "Operation", "");
}

static void def_rgb_curve(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "mapping", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "storage");
	RNA_def_property_struct_type(prop, "CurveMapping");
	RNA_def_property_ui_text(prop, "Mapping", "");
}

static void def_vector_curve(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "mapping", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "storage");
	RNA_def_property_struct_type(prop, "CurveMapping");
	RNA_def_property_ui_text(prop, "Mapping", "");
}

static void def_time(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "storage");
	RNA_def_property_struct_type(prop, "CurveMapping");
	RNA_def_property_ui_text(prop, "Curve", "");
	
	prop = RNA_def_property(srna, "start", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Start Frame", "");
	
	prop = RNA_def_property(srna, "end", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom2");
	RNA_def_property_ui_text(prop, "End Frame", "");
}

static void def_val_to_rgb(StructRNA *srna)
{
	/*PropertyRNA *prop;*/
	
	/* TODO: uncomment when ColorBand is wrapped *//*
	prop = RNA_def_property(srna, "color_band", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "storage");
	RNA_def_property_struct_type(prop, "ColorBand");
	RNA_def_property_ui_text(prop, "Color Band", "");*/
}

static void def_mix_rgb(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem blend_type_items[] = {
		{ 0, "MIX",        0, "Mix",         ""},
		{ 1, "ADD",        0, "Add",         ""},
		{ 3, "SUBTRACT",   0, "Subtract",    ""},
		{ 2, "MULTIPLY",   0, "Multiply",    ""},
		{ 4, "SCREEN",     0, "Screen",      ""},
		{ 9, "OVERLAY",    0, "Overlay",     ""},
		{ 5, "DIVIDE",     0, "Divide",      ""},
		{ 6, "DIFFERENCE", 0, "Difference",  ""},
		{ 7, "DARKEN",     0, "Darken",      ""},
		{ 8, "LIGHTEN",    0, "Lighten",     ""},
		{10, "DODGE",      0, "Dodge",       ""},
		{11, "BURN",       0, "Burn",        ""},
		{15, "COLOR",      0, "Color",       ""},
		{14, "VALUE",      0, "Value",       ""},
		{13, "SATURATION", 0, "Saturation",  ""},
		{12, "HUE",        0, "Hue",         ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "blend_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, blend_type_items);
	RNA_def_property_ui_text(prop, "Blend Type", "");
	
	prop = RNA_def_property(srna, "alpha", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom2", 1);
	RNA_def_property_ui_text(prop, "Diffuse", "Include alpha of second input in this operation");
}

static void def_texture(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "texture", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "id");
	RNA_def_property_struct_type(prop, "Texture");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Texture", "");
	
	prop = RNA_def_property(srna, "node_output", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Node Output", "For node-based textures, which output node to use");
}


/* -- Shader Nodes ---------------------------------------------------------- */

static void def_sh_material(StructRNA *srna)
{
	PropertyRNA *prop;

	prop = RNA_def_property(srna, "material", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "id");
	RNA_def_property_struct_type(prop, "Material");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Material", "");

	prop = RNA_def_property(srna, "diffuse", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", SH_NODE_MAT_DIFF);
	RNA_def_property_ui_text(prop, "Diffuse", "Material Node outputs Diffuse");

	prop = RNA_def_property(srna, "specular", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", SH_NODE_MAT_SPEC);
	RNA_def_property_ui_text(prop, "Specular", "Material Node outputs Specular");
	
	prop = RNA_def_property(srna, "invert_normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", SH_NODE_MAT_NEG);
	RNA_def_property_ui_text(prop, "Invert Normal", "Material Node uses inverted normal");
}

static void def_sh_mapping(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "mapping", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "storage");
	RNA_def_property_struct_type(prop, "TexMapping");
	RNA_def_property_ui_text(prop, "Mapping", "");
}

static void def_sh_geometry(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeGeometry", "storage");
	
	prop = RNA_def_property(srna, "uv_layer", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "uvname");
	RNA_def_property_ui_text(prop, "UV Layer", "");
	
	prop = RNA_def_property(srna, "color_layer", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "colname");
	RNA_def_property_ui_text(prop, "Vertex Color Layer", "");
}


/* -- Compositor Nodes ------------------------------------------------------ */

static void def_cmp_alpha_over(StructRNA *srna)
{
	PropertyRNA *prop;

	prop = RNA_def_property(srna, "convert_premul", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", 1);
	RNA_def_property_ui_text(prop, "convert_premul", "TODO: don't know what this is");
	
	RNA_def_struct_sdna_from(srna, "NodeTwoFloats", "storage");
	
	prop = RNA_def_property(srna, "premul", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "x");
	RNA_def_property_ui_text(prop, "Premul", "Mix Factor");
}

static void def_cmp_blur(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem filter_type_items[] = {
		{R_FILTER_BOX,        "FLAT",       0, "Flat",          ""},
		{R_FILTER_TENT,       "TENT",       0, "Tent",          ""},
		{R_FILTER_QUAD,       "QUAD",       0, "Quadratic",     ""},
		{R_FILTER_CUBIC,      "CUBIC",      0, "Cubic",         ""},
		{R_FILTER_GAUSS,      "GAUSS",      0, "Gaussian",      ""},
		{R_FILTER_FAST_GAUSS, "FAST_GAUSS", 0, "Fast Gaussian", ""},
		{R_FILTER_CATROM,     "CATROM",     0, "Catrom",        ""},
		{R_FILTER_MITCH,      "MITCH",      0, "Mitch",         ""},
		{0, NULL, 0, NULL, NULL}
	};

	RNA_def_struct_sdna_from(srna, "NodeBlurData", "storage");
	
	prop = RNA_def_property(srna, "sizex", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "sizex");
	RNA_def_property_ui_text(prop, "Size X", "");
	
	prop = RNA_def_property(srna, "sizey", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "sizey");
	RNA_def_property_ui_text(prop, "Size Y", "");
	
	prop = RNA_def_property(srna, "samples", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "samples");
	RNA_def_property_ui_text(prop, "Samples", "");
	
	prop = RNA_def_property(srna, "max_speed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "maxspeed");
	RNA_def_property_ui_text(prop, "Max Speed", "");
	
	prop = RNA_def_property(srna, "min_speed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "minspeed");
	RNA_def_property_ui_text(prop, "Min Speed", "");
	
	prop = RNA_def_property(srna, "relative", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "relative", 1);
	RNA_def_property_ui_text(prop, "Relative", "");
	
	prop = RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fac");
	RNA_def_property_ui_text(prop, "Factor", "");
	
	prop = RNA_def_property(srna, "factor_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "percentx");
	RNA_def_property_ui_text(prop, "Relative Size X", "");
	
	prop = RNA_def_property(srna, "factor_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "percenty");
	RNA_def_property_ui_text(prop, "Relative Size Y", "");
	
	prop = RNA_def_property(srna, "filter_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "filtertype");
	RNA_def_property_enum_items(prop, filter_type_items);
	RNA_def_property_ui_text(prop, "Filter Type", "");
	
	prop = RNA_def_property(srna, "bokeh", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "bokeh", 1);
	RNA_def_property_ui_text(prop, "Bokeh", "");
	
	prop = RNA_def_property(srna, "gamma", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gamma", 1);
	RNA_def_property_ui_text(prop, "Gamma", "");
	
	/*
		TODO:
			curved
			image_in_width
			image_in_height
			
		Don't know if these need wrapping, can't find them in interface
	*/
	
}

static void def_cmp_filter(StructRNA *srna)
{
	PropertyRNA *prop;

	static EnumPropertyItem type_items[] = {
		{0, "SOFTEN",  0, "Soften",  ""},
		{1, "SHARPEN", 0, "Sharpen", ""},
		{2, "LAPLACE", 0, "Laplace", ""},
		{3, "SOBEL",   0, "Sobel",   ""},
		{4, "PREWITT", 0, "Prewitt", ""},
		{5, "KIRSCH",  0, "Kirsch",  ""},
		{6, "SHADOW",  0, "Shadow",  ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Type", "");
}

static void def_cmp_map_value(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "TexMapping", "storage");
	
	prop = RNA_def_property(srna, "offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "loc");
	RNA_def_property_ui_text(prop, "Offset", "");
	
	prop = RNA_def_property(srna, "size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Size", "");
	
	prop = RNA_def_property(srna, "use_min", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TEXMAP_CLIP_MIN);
	RNA_def_property_ui_text(prop, "Use Minimum", "");
	
	prop = RNA_def_property(srna, "use_max", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TEXMAP_CLIP_MAX);
	RNA_def_property_ui_text(prop, "Use Maximum", "");
	
	prop = RNA_def_property(srna, "min", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "min");
	RNA_def_property_ui_text(prop, "Minimum", "");
	
	prop = RNA_def_property(srna, "max", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "max");
	RNA_def_property_ui_text(prop, "Maximum", "");
}

static void def_cmp_vector_blur(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeBlurData", "storage");
	
	prop = RNA_def_property(srna, "samples", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "samples");
	RNA_def_property_ui_text(prop, "Samples", "");
	
	prop = RNA_def_property(srna, "min_speed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "minspeed");
	RNA_def_property_ui_text(prop, "Min Speed", "Minimum speed for a pixel to be blurred; used to separate background from foreground");
		
	prop = RNA_def_property(srna, "max_speed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "maxspeed");
	RNA_def_property_ui_text(prop, "Min Speed", "Maximum speed, or zero for none");
	
	prop = RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fac");
	RNA_def_property_ui_text(prop, "Blur Factor", "Scaling factor for motion vectors; actually 'shutter speed' in frames");
	
	prop = RNA_def_property(srna, "curved", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "curved", 1);
	RNA_def_property_ui_text(prop, "Curved", "Interpolate between frames in a bezier curve, rather than linearly");
}

static void def_cmp_image(StructRNA *srna)
{
	PropertyRNA *prop;
	
	/*static EnumPropertyItem type_items[] = {
		{IMA_SRC_FILE,      "IMAGE",     0, "Image",     ""},
		{IMA_SRC_MOVIE,     "MOVIE",     "Movie",     ""},
		{IMA_SRC_SEQUENCE,  "SEQUENCE",  "Sequence",  ""},
		{IMA_SRC_GENERATED, "GENERATED", "Generated", ""},
		{0, NULL, 0, NULL, NULL}
	};*/
	
	prop = RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "id");
	RNA_def_property_struct_type(prop, "Image");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Image", "");
	
	RNA_def_struct_sdna_from(srna, "ImageUser", "storage");

	/* TODO: if movie or sequence { */
	
	prop = RNA_def_property(srna, "frames", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "frames");
	RNA_def_property_ui_text(prop, "Frames", "Number of images used in animation");
	
	prop = RNA_def_property(srna, "start", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "sfra");
	RNA_def_property_ui_text(prop, "Start Frame", "");
	
	prop = RNA_def_property(srna, "offset", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "offset");
	RNA_def_property_ui_text(prop, "Offset", "Offsets the number of the frame to use in the animation");
	
	prop = RNA_def_property(srna, "cyclic", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "cycl", 1);
	RNA_def_property_ui_text(prop, "Cyclic", "");
	
	prop = RNA_def_property(srna, "auto_refresh", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", IMA_ANIM_ALWAYS);
	RNA_def_property_ui_text(prop, "Auto-Refresh", "");
	
	/* } */
	
	/* if type == multilayer { */
	
	prop = RNA_def_property(srna, "layer", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "layer");
	RNA_def_property_ui_text(prop, "Layer", "");
	
	/* } */
	
	/* TODO: refresh on change */
	
}

static void def_cmp_render_layers(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "scene", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "id");
	RNA_def_property_struct_type(prop, "Scene");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Scene", "");
	
	/* TODO: layers in menu */
	prop = RNA_def_property(srna, "layer", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Layer", "");
	
	/* TODO: comments indicate this might be a hack */
	prop = RNA_def_property(srna, "re_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom2", 1);
	RNA_def_property_ui_text(prop, "Re-render", "");
}

static void def_cmp_output_file(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem type_items[] = {
		{R_TARGA,   "TARGA",        0, "Targa",        ""},
		{R_RAWTGA,  "RAW_TARGA",    0, "Targa Raw",    ""},
		{R_PNG,     "PNG",          0, "PNG",          ""},
		{R_BMP,     "BMP",          0, "BMP",          ""},
		{R_JPEG90,  "JPEG",         0, "JPEG",         ""},
		{R_IRIS,    "IRIS",         0, "IRIS",         ""},
		{R_RADHDR,  "RADIANCE_HDR", 0, "Radiance HDR", ""},
		{R_CINEON,  "CINEON",       0, "Cineon",       ""},
		{R_DPX,     "DPX",          0, "DPX",          ""},
		{R_OPENEXR, "OPENEXR",      0, "OpenEXR",      ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	static EnumPropertyItem openexr_codec_items[] = {
		{0, "NONE",  0, "None",           ""},
		{1, "PXR24", 0, "Pxr24 (lossy)",  ""},
		{2, "ZIP",   0, "ZIP (lossless)", ""},
		{3, "PIZ",   0, "PIX (lossless)", ""},
		{4, "RLE",   0, "RLE (lossless)", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	RNA_def_struct_sdna_from(srna, "NodeImageFile", "storage");
	
	prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "name");
	RNA_def_property_ui_text(prop, "Name", "");
	
	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "imtype");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Type", "");
	
	/* TODO: openexr only { */
	
	prop = RNA_def_property(srna, "half", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "subimtype", R_OPENEXR_HALF);
	RNA_def_property_ui_text(prop, "Half", "");
	
	prop = RNA_def_property(srna, "codec", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "codec");
	RNA_def_property_enum_items(prop, openexr_codec_items);
	RNA_def_property_ui_text(prop, "Codec", "");
	
	/* } else { */
	
	prop = RNA_def_property(srna, "quality", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "quality");
	RNA_def_property_ui_text(prop, "Quality", "");
	
	/* } */
	
	prop = RNA_def_property(srna, "start", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "sfra");
	RNA_def_property_ui_text(prop, "Start Frame", "");
	
	prop = RNA_def_property(srna, "end", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "efra");
	RNA_def_property_ui_text(prop, "End Frame", "");
}

static void def_cmp_dilate_erode(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "distance", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom2");
	RNA_def_property_ui_text(prop, "Distance", "Distance to grow/shrink (number of iterations)");
}

static void def_cmp_scale(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem space_items[] = {
		{0, "RELATIVE",   0, "Relative",   ""},
		{1, "ABSOLUTE",   0, "Absolute",   ""},
		{2, "SCENE_SIZE", 0, "Scene Size", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "space", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, space_items);
	RNA_def_property_ui_text(prop, "Space", "Coordinate space to scale relative to");
}

static void def_cmp_diff_matte(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem color_space_items[] = {
		{1, "RGB", 0, "RGB",   ""},
		{2, "HSV", 0, "HSV",   ""},
		{3, "YUV", 0, "YUV",   ""},
		{4, "YCC", 0, "YCbCr", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "color_space", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, color_space_items);
	RNA_def_property_ui_text(prop, "Color Space", "");
	
	RNA_def_struct_sdna_from(srna, "NodeChroma", "storage");
	
	/* TODO: nicer wrapping for tolerances */
	
	prop = RNA_def_property(srna, "tolerance1", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t1");
	RNA_def_property_ui_text(prop, "Channel 1 Tolerance", "");
	
	prop = RNA_def_property(srna, "tolerance2", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t2");
	RNA_def_property_ui_text(prop, "Channel 2 Tolerance", "");
	
	prop = RNA_def_property(srna, "tolerance3", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t3");
	RNA_def_property_ui_text(prop, "Channel 3 Tolerance", "");
	
	prop = RNA_def_property(srna, "falloff", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fstrength");
	RNA_def_property_ui_text(prop, "Falloff", "");
}

static void def_cmp_color_spill(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem channel_items[] = {
		{1, "R", 0, "Red",   ""},
		{2, "G", 0, "Green", ""},
		{3, "B", 0, "Blue",  ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "channel", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, channel_items);
	RNA_def_property_ui_text(prop, "Channel", "");
	
	RNA_def_struct_sdna_from(srna, "NodeChroma", "storage");
	
	prop = RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t1");
	RNA_def_property_ui_text(prop, "Amount", "How much the selected channel is affected by");
}

static void def_cmp_chroma(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeChroma", "storage");
	
	prop = RNA_def_property(srna, "acceptance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t1");
	RNA_def_property_ui_text(prop, "Acceptance", "Tolerance for a color to be considered a keying color");
	
	prop = RNA_def_property(srna, "cutoff", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t2");
	RNA_def_property_ui_text(prop, "Cutoff", "Tolerance below which colors will be considered as exact matches");

	prop = RNA_def_property(srna, "lift", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fsize");
	RNA_def_property_ui_text(prop, "Lift", "Alpha lift");
	
	prop = RNA_def_property(srna, "gain", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fstrength");
	RNA_def_property_ui_text(prop, "Gain", "Alpha gain");
	
	prop = RNA_def_property(srna, "shadow_adjust", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t3");
	RNA_def_property_ui_text(prop, "Shadow Adjust", "Adjusts the brightness of any shadows captured");
	
	/* TODO: 
		if(c->t2 > c->t1)
			c->t2=c->t1;
	*/
}

static void def_cmp_channel_matte(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem color_space_items[] = {
		{1, "RGB", 0, "RGB",   ""},
		{2, "HSV", 0, "HSV",   ""},
		{3, "YUV", 0, "YUV",   ""},
		{4, "YCC", 0, "YCbCr", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "color_space", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, color_space_items);
	RNA_def_property_ui_text(prop, "Color Space", "");
	
	/* TODO: channel must be 1, 2 or 3 */
	prop = RNA_def_property(srna, "channel", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom2");
	RNA_def_property_ui_text(prop, "Channel", "");
	
	RNA_def_struct_sdna_from(srna, "NodeChroma", "storage");
	
	prop = RNA_def_property(srna, "high", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t1");
	RNA_def_property_ui_text(prop, "High", "Values higher than this setting are 100% opaque");
	
	prop = RNA_def_property(srna, "low", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t2");
	RNA_def_property_ui_text(prop, "Low", "Values lower than this setting are 100% keyed");
	
	/* TODO:
		if(c->t2 > c->t1)
			c->t2=c->t1;
	*/
}

static void def_cmp_flip(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem axis_items[] = {
		{0, "X",  0, "X",     ""},
		{1, "Y",  0, "Y",     ""},
		{2, "XY", 0, "X & Y", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, axis_items);
	RNA_def_property_ui_text(prop, "Axis", "");
}

static void def_cmp_splitviewer(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem axis_items[] = {
		{0, "X",  0, "X",     ""},
		{1, "Y",  0, "Y",     ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom2");
	RNA_def_property_enum_items(prop, axis_items);
	RNA_def_property_ui_text(prop, "Axis", "");
	
	/* TODO: percentage */
	prop = RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Factor", "");
}

static void def_cmp_id_mask(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Index", "Pass index number to convert to alpha");
}

static void def_cmp_map_uv(StructRNA *srna)
{
	PropertyRNA *prop;
	
	/* TODO: percentage */
	prop = RNA_def_property(srna, "alpha", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Alpha", "");
}

static void def_cmp_defocus(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem bokeh_items[] = {
		{8, "OCTAGON",  0, "Octagonal",  "8 sides"},
		{7, "HEPTAGON", 0, "Heptagonal", "7 sides"},
		{6, "HEXAGON",  0, "Hexagonal",  "6 sides"},
		{5, "PENTAGON", 0, "Pentagonal", "5 sides"},
		{4, "SQUARE",   0, "Square",     "4 sides"},
		{3, "TRIANGLE", 0, "Triangular", "3 sides"},
		{0, "CIRCLE",   0, "Circular",   ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	RNA_def_struct_sdna_from(srna, "NodeDefocus", "storage");
	
	prop = RNA_def_property(srna, "bokeh", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "bktype");
	RNA_def_property_enum_items(prop, bokeh_items);
	RNA_def_property_ui_text(prop, "Bokeh Type", "");

	/* TODO: angle in degrees */		
	prop = RNA_def_property(srna, "angle", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "rotation");
	RNA_def_property_ui_text(prop, "Angle", "Bokeh shape rotation offset in degrees");
	
	prop = RNA_def_property(srna, "gamma_correction", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gamco", 1);
	RNA_def_property_ui_text(prop, "Gamma Correction", "Enable gamma correction before and after main process");

	/* TODO */
	prop = RNA_def_property(srna, "f_stop", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fstop");
	RNA_def_property_ui_text(prop, "fStop", "Amount of focal blur, 128=infinity=perfect focus, half the value doubles the blur radius");
	
	prop = RNA_def_property(srna, "max_blur", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "maxblur");
	RNA_def_property_ui_text(prop, "Max Blur", "blur limit, maximum CoC radius, 0=no limit");
	
	prop = RNA_def_property(srna, "threshold", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "bthresh");
	RNA_def_property_ui_text(prop, "Threshold", "CoC radius threshold, prevents background bleed on in-focus midground, 0=off");
	
	prop = RNA_def_property(srna, "preview", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "preview", 1);
	RNA_def_property_ui_text(prop, "Preview", "Enable sampling mode, useful for preview when using low samplecounts");
	
	prop = RNA_def_property(srna, "samples", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "samples");
	RNA_def_property_ui_text(prop, "Samples", "Number of samples (16=grainy, higher=less noise)");
	
	prop = RNA_def_property(srna, "use_zbuffer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "no_zbuf", 1);
	RNA_def_property_ui_text(prop, "Use Z-Buffer", "Disable when using an image as input instead of actual zbuffer (auto enabled if node not image based, eg. time node)");
	
	prop = RNA_def_property(srna, "z_scale", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "scale");
	RNA_def_property_ui_text(prop, "Z-Scale", "Scales the Z input when not using a zbuffer, controls maximum blur designated by the color white or input value 1");
}

static void def_cmp_luma_matte(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeChroma", "storage");
	
	prop = RNA_def_property(srna, "high", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t1");
	RNA_def_property_ui_text(prop, "High", "Values higher than this setting are 100% opaque");
	
	prop = RNA_def_property(srna, "low", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "t2");
	RNA_def_property_ui_text(prop, "Low", "Values lower than this setting are 100% keyed");
	
	/* TODO: keep low less than high */
	
}

static void def_cmp_invert(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "rgb", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", CMP_CHAN_RGB);
	RNA_def_property_ui_text(prop, "RGB", "");
	
	prop = RNA_def_property(srna, "alpha", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", CMP_CHAN_A);
	RNA_def_property_ui_text(prop, "Alpha", "");
}

static void def_cmp_crop(StructRNA *srna)
{
	PropertyRNA *prop;
	
	prop = RNA_def_property(srna, "crop_size", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "custom1", 1);
	RNA_def_property_ui_text(prop, "Crop Image Size", "Whether to crop the size of the input image");
	
	RNA_def_struct_sdna_from(srna, "NodeTwoXYs", "storage");

	prop = RNA_def_property(srna, "x1", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "x1");
	RNA_def_property_ui_text(prop, "X1", "");
	
	prop = RNA_def_property(srna, "x2", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "x2");
	RNA_def_property_ui_text(prop, "X2", "");
	
	prop = RNA_def_property(srna, "y1", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "y1");
	RNA_def_property_ui_text(prop, "Y1", "");
	
	prop = RNA_def_property(srna, "y2", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "y2");
	RNA_def_property_ui_text(prop, "Y2", "");
}

static void def_cmp_dblur(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeDBlurData", "storage");
	
	prop = RNA_def_property(srna, "iterations", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "iter");
	RNA_def_property_ui_text(prop, "Iterations", "");
	
	prop = RNA_def_property(srna, "wrap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "wrap", 1);
	RNA_def_property_ui_text(prop, "Wrap", "");
	
	prop = RNA_def_property(srna, "center_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "center_x");
	RNA_def_property_ui_text(prop, "Center X", "");
	
	prop = RNA_def_property(srna, "center_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "center_y");
	RNA_def_property_ui_text(prop, "Center Y", "");
	
	prop = RNA_def_property(srna, "distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "distance");
	RNA_def_property_ui_text(prop, "Distance", "");
	
	prop = RNA_def_property(srna, "angle", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "angle");
	RNA_def_property_ui_text(prop, "Angle", "");
	
	prop = RNA_def_property(srna, "spin", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "spin");
	RNA_def_property_ui_text(prop, "Spin", "");
	
	prop = RNA_def_property(srna, "zoom", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zoom");
	RNA_def_property_ui_text(prop, "Zoom", "");
}

static void def_cmp_bilateral_blur(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeBilateralBlurData", "storage");
	
	prop = RNA_def_property(srna, "iterations", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "iter");
	RNA_def_property_ui_text(prop, "Iterations", "");
	
	prop = RNA_def_property(srna, "sigma_color", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "sigma_color");
	RNA_def_property_ui_text(prop, "Color Sigma", "");
	
	prop = RNA_def_property(srna, "sigma_space", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "sigma_space");
	RNA_def_property_ui_text(prop, "Space Sigma", "");
	
}

static void def_cmp_premul_key(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem type_items[] = {
		{0, "KEY_TO_PREMUL", 0, "Key to Premul", ""},
		{1, "PREMUL_TO_KEY", 0, "Premul to Key", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "custom1");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Blend Type", "Conversion between premultiplied alpha and key alpha");
	
}

static void def_cmp_glare(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem type_items[] = {
		{3, "GHOSTS",      0, "Ghosts",      ""},
		{2, "STREAKS",     0, "Streaks",     ""},
		{1, "FOG_GLOW",    0, "Fog Glow",    ""},
		{0, "SIMPLE_STAR", 0, "Simple Star", ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	/*static EnumPropertyItem quality_items[] = {
		{0, "HIGH",   0, "High",   ""},
		{1, "MEDIUM", 0, "Medium", ""},
		{2, "LOW",    0, "Low",    ""},
		{0, NULL, 0, NULL, NULL}
	};*/
	
	RNA_def_struct_sdna_from(srna, "NodeGlare", "storage");
	
	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Type", "");
	
	prop = RNA_def_property(srna, "quality", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "quality");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Quality", "If not set to high quality, the effect will be applied to a low-res copy of the source image");
	
	prop = RNA_def_property(srna, "iterations", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "iter");
	RNA_def_property_ui_text(prop, "Iterations", "");
	
	prop = RNA_def_property(srna, "color_modulation", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "colmod");
	RNA_def_property_ui_text(prop, "Color Modulation", "");
	
	prop = RNA_def_property(srna, "mix", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mix");
	RNA_def_property_ui_text(prop, "Mix", "-1 is original image only, 0 is exact 50/50 mix, 1 is processed image only");
	
	prop = RNA_def_property(srna, "threshold", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "threshold");
	RNA_def_property_ui_text(prop, "Threshold", "The glare filter will only be applied to pixels brighter than this value");
	
	prop = RNA_def_property(srna, "streaks", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "angle");
	RNA_def_property_ui_text(prop, "Streaks", "Total number of streaks");
	
	prop = RNA_def_property(srna, "angle_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "angle_ofs");
	RNA_def_property_ui_text(prop, "Angle Offset", "Streak angle offset in degrees");
	
	prop = RNA_def_property(srna, "fade", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fade");
	RNA_def_property_ui_text(prop, "Fade", "Streak fade-out factor");
	
	prop = RNA_def_property(srna, "rotate_45", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "angle", 1);
	RNA_def_property_ui_text(prop, "Rotate 45", "Simple star filter: add 45 degree rotation offset");
	
	prop = RNA_def_property(srna, "size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Size", "Glow/glare size (not actual size; relative to initial size of bright area of pixels)");
	
	/* TODO */
}

static void def_cmp_tonemap(StructRNA *srna)
{
	PropertyRNA *prop;
	
	static EnumPropertyItem type_items[] = {
		{1, "RD_PHOTORECEPTOR", 0, "R/D Photoreceptor", ""},
		{0, "RH_SIMPLE",        0, "Rh Simple",         ""},
		{0, NULL, 0, NULL, NULL}
	};
	
	RNA_def_struct_sdna_from(srna, "NodeTonemap", "storage");
	
	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Type", "");
	
	/* TODO: if type==0 { */
	
	prop = RNA_def_property(srna, "key", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "key");
	RNA_def_property_ui_text(prop, "Key", "The value the average luminance is mapped to");
	
	prop = RNA_def_property(srna, "offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "offset");
	RNA_def_property_ui_text(prop, "Offset", "Normally always 1, but can be used as an extra control to alter the brightness curve");
	
	prop = RNA_def_property(srna, "gamma", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "gamma");
	RNA_def_property_ui_text(prop, "Gamma", "If not used, set to 1");
	
	/* TODO: } else { */
	
	prop = RNA_def_property(srna, "intensity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "f");
	RNA_def_property_ui_text(prop, "Intensity", "If less than zero, darkens image; otherwise, makes it brighter");
	
	prop = RNA_def_property(srna, "contrast", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "m");
	RNA_def_property_ui_text(prop, "Contrast", "Set to 0 to use estimate from input image");
	
	prop = RNA_def_property(srna, "adaptation", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "a");
	RNA_def_property_ui_text(prop, "Adaptation", "If 0, global; if 1, based on pixel intensity");
	
	prop = RNA_def_property(srna, "correction", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "c");
	RNA_def_property_ui_text(prop, "Color Correction", "If 0, same for all channels; if 1, each independent");
}

static void def_cmp_lensdist(StructRNA *srna)
{
	PropertyRNA *prop;
	
	RNA_def_struct_sdna_from(srna, "NodeLensDist", "storage");
	
	prop = RNA_def_property(srna, "projector", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "proj", 1);
	RNA_def_property_ui_text(prop, "Projector", "Enable/disable projector mode. Effect is applied in horizontal direction only.");
	
	/* TODO: if proj mode is off { */
	
	prop = RNA_def_property(srna, "jitter", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "jit", 1);
	RNA_def_property_ui_text(prop, "Jitter", "Enable/disable jittering; faster, but also noisier");
	
	prop = RNA_def_property(srna, "fit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "fit", 1);
	RNA_def_property_ui_text(prop, "Fit", "For positive distortion factor only: scale image such that black areas are not visible");
}
	


/* -- Texture Nodes --------------------------------------------------------- */

static void def_tex_output(StructRNA *srna)
{
	PropertyRNA *prop;

	RNA_def_struct_sdna_from(srna, "TexNodeOutput", "storage");
	
	prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "name");
	RNA_def_property_ui_text(prop, "Name", "");
}

static void def_tex_image(StructRNA *srna)
{
	PropertyRNA *prop;

	prop = RNA_def_property(srna, "settings", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "storage");
	RNA_def_property_struct_type(prop, "ImageUser");
	RNA_def_property_ui_text(prop, "Settings", "");
}

static void def_tex_bricks(StructRNA *srna)
{
	PropertyRNA *prop;

	prop = RNA_def_property(srna, "offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "custom3");
	RNA_def_property_ui_text(prop, "Offset Amount", "");
	
	prop = RNA_def_property(srna, "offset_frequency", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom1");
	RNA_def_property_ui_text(prop, "Offset Frequency", "Offset every N rows");
	
	prop = RNA_def_property(srna, "squash", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "custom4");
	RNA_def_property_ui_text(prop, "Squash Amount", "");
	
	prop = RNA_def_property(srna, "squash_frequency", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "custom2");
	RNA_def_property_ui_text(prop, "Squash Frequency", "Squash every N rows");
}

/* -------------------------------------------------------------------------- */

static void rna_def_shader_node(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	EnumPropertyItem *node_type_items;
	
	node_type_items = alloc_node_type_items(Category_ShaderNode);

	srna = RNA_def_struct(brna, "ShaderNode", "Node");
	RNA_def_struct_ui_text(srna, "Shader Node", "Material shader node.");
	RNA_def_struct_sdna(srna, "bNode");

	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_enum_items(prop, node_type_items);
	RNA_def_property_ui_text(prop, "Type", "");
}

static void rna_def_compositor_node(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	EnumPropertyItem *node_type_items;
	
	node_type_items = alloc_node_type_items(Category_CompositorNode);
	
	srna = RNA_def_struct(brna, "CompositorNode", "Node");
	RNA_def_struct_ui_text(srna, "Compositor Node", "");
	RNA_def_struct_sdna(srna, "bNode");

	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_enum_items(prop, node_type_items);
	RNA_def_property_ui_text(prop, "Type", "");
}

static void rna_def_texture_node(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	EnumPropertyItem *node_type_items;
	
	node_type_items = alloc_node_type_items(Category_TextureNode);
	
	srna = RNA_def_struct(brna, "TextureNode", "Node");
	RNA_def_struct_ui_text(srna, "Texture Node", "");
	RNA_def_struct_sdna(srna, "bNode");

	prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_enum_items(prop, node_type_items);
	RNA_def_property_ui_text(prop, "Type", "");
}

/* -------------------------------------------------------------------------- */

static void rna_def_node(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna = RNA_def_struct(brna, "Node", NULL);
	RNA_def_struct_ui_text(srna, "Node", "Node in a node tree.");
	RNA_def_struct_sdna(srna, "bNode");
	RNA_def_struct_refine_func(srna, "rna_Node_refine");
	
	prop = RNA_def_property(srna, "location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "locx");
	RNA_def_property_array(prop, 2);
	RNA_def_property_range(prop, -10000.0f, 10000.0f);
	RNA_def_property_ui_text(prop, "Location", "");
	
	prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Node name.");
	RNA_def_struct_name_property(srna, prop);
}

static void rna_def_nodetree(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna = RNA_def_struct(brna, "NodeTree", "ID");
	RNA_def_struct_ui_text(srna, "Node Tree", "Node tree consisting of linked nodes used for materials, textures and compositing.");
	RNA_def_struct_sdna(srna, "bNodeTree");
	RNA_def_struct_ui_icon(srna, ICON_NODE);

	prop = RNA_def_property(srna, "nodes", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "nodes", NULL);
	RNA_def_property_struct_type(prop, "Node");
	RNA_def_property_ui_text(prop, "Nodes", "");
}

static void define_specific_node(BlenderRNA *brna, int id, void (*func)(StructRNA*))
{
	StructRNA *srna = def_node(brna, id);
	
	if(func)
		func(srna);
}

void RNA_def_nodetree(BlenderRNA *brna)
{
	init();
	rna_def_nodetree(brna);
	rna_def_node(brna);
	rna_def_shader_node(brna);
	rna_def_compositor_node(brna);
	rna_def_texture_node(brna);
	
	#define DefNode(Category, ID, DefFunc, EnumName, StructName, UIName, UIDesc) \
		define_specific_node(brna, ID, DefFunc);
		
	#include "rna_nodetree_types.h"
	
	#undef DefNode
}

#endif

