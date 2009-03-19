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

#include "DNA_ID.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#ifdef RNA_RUNTIME

/* Struct */

static void rna_Struct_identifier_get(PointerRNA *ptr, char *value)
{
	strcpy(value, ((StructRNA*)ptr->data)->identifier);
}

static int rna_Struct_identifier_length(PointerRNA *ptr)
{
	return strlen(((StructRNA*)ptr->data)->identifier);
}

static void rna_Struct_description_get(PointerRNA *ptr, char *value)
{
	strcpy(value, ((StructRNA*)ptr->data)->description);
}

static int rna_Struct_description_length(PointerRNA *ptr)
{
	return strlen(((StructRNA*)ptr->data)->description);
}

static void rna_Struct_name_get(PointerRNA *ptr, char *value)
{
	strcpy(value, ((StructRNA*)ptr->data)->name);
}

static int rna_Struct_name_length(PointerRNA *ptr)
{
	return strlen(((StructRNA*)ptr->data)->name);
}

static PointerRNA rna_Struct_base_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_Struct, ((StructRNA*)ptr->data)->base);
}

static PointerRNA rna_Struct_nested_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_Struct, ((StructRNA*)ptr->data)->nested);
}

static PointerRNA rna_Struct_name_property_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_Property, ((StructRNA*)ptr->data)->nameproperty);
}

/* Struct property iteration. This is quite complicated, the purpose is to
 * iterate over properties of all inheritance levels, and for each struct to
 * also iterator over id properties not known by RNA. */

static int rna_idproperty_known(CollectionPropertyIterator *iter, void *data)
{
	IDProperty *idprop= (IDProperty*)data;
	PropertyRNA *prop;

	/* function to skip any id properties that are already known by RNA,
	 * for the second loop where we go over unknown id properties */

	for(prop= iter->parent.type->properties.first; prop; prop=prop->next)
		if(strcmp(prop->identifier, idprop->name) == 0)
			return 1;
	
	return 0;
}

static int rna_property_builtin(CollectionPropertyIterator *iter, void *data)
{
	PropertyRNA *prop= (PropertyRNA*)data;

	/* function to skip builtin rna properties */

	return (prop->flag & PROP_BUILTIN);
}

static void rna_inheritance_next_level_restart(CollectionPropertyIterator *iter, IteratorSkipFunc skip)
{
	/* RNA struct inheritance */
	while(!iter->valid && iter->level > 0) {
		StructRNA *srna;
		int i;

		srna= (StructRNA*)iter->parent.data;
		iter->level--;
		for(i=iter->level; i>0; i--)
			srna= srna->base;

		rna_iterator_listbase_end(iter);
		rna_iterator_listbase_begin(iter, &srna->properties, skip);
	}
}

static void rna_inheritance_listbase_begin(CollectionPropertyIterator *iter, ListBase *lb, IteratorSkipFunc skip)
{
	rna_iterator_listbase_begin(iter, lb, skip);
	rna_inheritance_next_level_restart(iter, skip);
}

static void rna_inheritance_listbase_next(CollectionPropertyIterator *iter, IteratorSkipFunc skip)
{
	rna_iterator_listbase_next(iter);
	rna_inheritance_next_level_restart(iter, skip);
}

static void rna_Struct_properties_next(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;
	IDProperty *group;

	if(internal->flag) {
		/* id properties */
		rna_iterator_listbase_next(iter);
	}
	else {
		/* regular properties */
		rna_inheritance_listbase_next(iter, rna_property_builtin);

		/* try id properties */
		if(!iter->valid) {
			group= rna_idproperties_get(&iter->parent, 0);

			if(group) {
				rna_iterator_listbase_end(iter);
				rna_iterator_listbase_begin(iter, &group->data.group, rna_idproperty_known);
				internal= iter->internal;
				internal->flag= 1;
			}
		}
	}
}

static void rna_Struct_properties_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	StructRNA *srna;

	/* here ptr->data should always be the same as iter->parent.type */
	srna= (StructRNA *)ptr->data;

	while(srna->base) {
		iter->level++;
		srna= srna->base;
	}

	rna_inheritance_listbase_begin(iter, &srna->properties, rna_property_builtin);
}

static PointerRNA rna_Struct_properties_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;

	/* we return either PropertyRNA* or IDProperty*, the rna_access.c
	 * functions can handle both as PropertyRNA* with some tricks */
	return rna_pointer_inherit_refine(&iter->parent, &RNA_Property, internal->link);
}

/* Builtin properties iterator re-uses the Struct properties iterator, only
 * difference is that we need to see the ptr data to the type of the struct
 * whose properties we want to iterate over. */

void rna_builtin_properties_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	PointerRNA newptr;

	/* we create a new pointer with the type as the data */
	newptr.type= &RNA_Struct;
	newptr.data= ptr->type;

	if(ptr->type->flag & STRUCT_ID)
		newptr.id.data= ptr->data;
	else
		newptr.id.data= NULL;

	iter->parent= newptr;

	rna_Struct_properties_begin(iter, &newptr);
}

void rna_builtin_properties_next(CollectionPropertyIterator *iter)
{
	rna_Struct_properties_next(iter);
}

PointerRNA rna_builtin_properties_get(CollectionPropertyIterator *iter)
{
	return rna_Struct_properties_get(iter);
}

PointerRNA rna_builtin_type_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_Struct, ptr->type);
}

/* Property */

static StructRNA *rna_Property_refine(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;

	rna_idproperty_check(&prop, ptr); /* XXX ptr? */

	switch(prop->type) {
		case PROP_BOOLEAN: return &RNA_BooleanProperty;
		case PROP_INT: return &RNA_IntProperty;
		case PROP_FLOAT: return &RNA_FloatProperty;
		case PROP_STRING: return &RNA_StringProperty;
		case PROP_ENUM: return &RNA_EnumProperty;
		case PROP_POINTER: return &RNA_PointerProperty;
		case PROP_COLLECTION: return &RNA_CollectionProperty;
		default: return &RNA_Property;
	}
}

static void rna_Property_identifier_get(PointerRNA *ptr, char *value)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	strcpy(value, ((PropertyRNA*)prop)->identifier);
}

static int rna_Property_identifier_length(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return strlen(prop->identifier);
}

static void rna_Property_name_get(PointerRNA *ptr, char *value)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	strcpy(value, prop->name);
}

static int rna_Property_name_length(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return strlen(prop->name);
}

static void rna_Property_description_get(PointerRNA *ptr, char *value)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	strcpy(value, prop->description);
}

static int rna_Property_description_length(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return strlen(prop->description);
}

static int rna_Property_type_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return prop->type;
}

static int rna_Property_subtype_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return prop->subtype;
}

static int rna_Property_editable_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	return RNA_property_editable(ptr, prop);
}

static int rna_Property_array_length_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return prop->arraylength;
}

static int rna_IntProperty_hard_min_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((IntPropertyRNA*)prop)->hardmin;
}

static int rna_IntProperty_hard_max_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((IntPropertyRNA*)prop)->hardmax;
}

static int rna_IntProperty_soft_min_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((IntPropertyRNA*)prop)->softmin;
}

static int rna_IntProperty_soft_max_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((IntPropertyRNA*)prop)->softmax;
}

static int rna_IntProperty_step_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((IntPropertyRNA*)prop)->step;
}

static float rna_FloatProperty_hard_min_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((FloatPropertyRNA*)prop)->hardmin;
}

static float rna_FloatProperty_hard_max_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((FloatPropertyRNA*)prop)->hardmax;
}

static float rna_FloatProperty_soft_min_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((FloatPropertyRNA*)prop)->softmin;
}

static float rna_FloatProperty_soft_max_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((FloatPropertyRNA*)prop)->softmax;
}

static float rna_FloatProperty_step_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((FloatPropertyRNA*)prop)->step;
}

static int rna_FloatProperty_precision_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((FloatPropertyRNA*)prop)->precision;
}

static int rna_StringProperty_max_length_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return ((StringPropertyRNA*)prop)->maxlength;
}

static void rna_EnumProperty_items_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	EnumPropertyRNA *eprop;

	rna_idproperty_check(&prop, ptr);
	eprop= (EnumPropertyRNA*)prop;

	rna_iterator_array_begin(iter, (void*)eprop->item, sizeof(eprop->item[0]), eprop->totitem, NULL);
}

static void rna_EnumPropertyItem_identifier_get(PointerRNA *ptr, char *value)
{
	strcpy(value, ((EnumPropertyItem*)ptr->data)->identifier);
}

static int rna_EnumPropertyItem_identifier_length(PointerRNA *ptr)
{
	return strlen(((EnumPropertyItem*)ptr->data)->identifier);
}

static void rna_EnumPropertyItem_name_get(PointerRNA *ptr, char *value)
{
	strcpy(value, ((EnumPropertyItem*)ptr->data)->name);
}

static int rna_EnumPropertyItem_name_length(PointerRNA *ptr)
{
	return strlen(((EnumPropertyItem*)ptr->data)->name);
}

static int rna_EnumPropertyItem_value_get(PointerRNA *ptr)
{
	return ((EnumPropertyItem*)ptr->data)->value;
}

static PointerRNA rna_PointerProperty_fixed_type_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return rna_pointer_inherit_refine(ptr, &RNA_Struct, ((PointerPropertyRNA*)prop)->structtype);
}

static PointerRNA rna_CollectionProperty_fixed_type_get(PointerRNA *ptr)
{
	PropertyRNA *prop= (PropertyRNA*)ptr->data;
	rna_idproperty_check(&prop, ptr);
	return rna_pointer_inherit_refine(ptr, &RNA_Struct, ((CollectionPropertyRNA*)prop)->structtype);
}

/* Blender RNA */

static void rna_BlenderRNA_structs_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	rna_iterator_listbase_begin(iter, &((BlenderRNA*)ptr->data)->structs, NULL);
}

#else

static void rna_def_struct(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Struct", NULL);
	RNA_def_struct_ui_text(srna, "Struct Definition", "RNA structure definition");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Struct_name_get", "rna_Struct_name_length", NULL);
	RNA_def_property_ui_text(prop, "Name", "Human readable name.");

	prop= RNA_def_property(srna, "identifier", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Struct_identifier_get", "rna_Struct_identifier_length", NULL);
	RNA_def_property_ui_text(prop, "Identifier", "Unique name used in the code and scripting.");
	RNA_def_struct_name_property(srna, prop);
	
	prop= RNA_def_property(srna, "description", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Struct_description_get", "rna_Struct_description_length", NULL);
	RNA_def_property_ui_text(prop, "Description", "Description of the Struct's purpose.");
	
	prop= RNA_def_property(srna, "base", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "Struct");
	RNA_def_property_pointer_funcs(prop, "rna_Struct_base_get", NULL);
	RNA_def_property_ui_text(prop, "Base", "Struct definition this is derived from.");

	prop= RNA_def_property(srna, "nested", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "Struct");
	RNA_def_property_pointer_funcs(prop, "rna_Struct_nested_get", NULL);
	RNA_def_property_ui_text(prop, "Nested", "Struct in which this struct is always nested, and to which it logically belongs.");

	prop= RNA_def_property(srna, "name_property", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "StringProperty");
	RNA_def_property_pointer_funcs(prop, "rna_Struct_name_property_get", NULL);
	RNA_def_property_ui_text(prop, "Name Property", "Property that gives the name of the struct.");

	prop= RNA_def_property(srna, "properties", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "Property");
	RNA_def_property_collection_funcs(prop, "rna_Struct_properties_begin", "rna_Struct_properties_next", "rna_iterator_listbase_end", "rna_Struct_properties_get", 0, 0, 0);
	RNA_def_property_ui_text(prop, "Properties", "Properties in the struct.");
}

static void rna_def_property(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	static EnumPropertyItem type_items[] = {
		{PROP_BOOLEAN, "BOOLEAN", "Boolean", ""},
		{PROP_INT, "INT", "Integer", ""},
		{PROP_FLOAT, "FLOAT", "Float", ""},
		{PROP_STRING, "STRING", "String", ""},
		{PROP_ENUM, "ENUM", "Enumeration", ""},
		{PROP_POINTER, "POINTER", "Pointer", ""},
		{PROP_COLLECTION, "COLLECTION", "Collection", ""},
		{0, NULL, NULL, NULL}};
	static EnumPropertyItem subtype_items[] = {
		{PROP_NONE, "NONE", "None", ""},
		{PROP_UNSIGNED, "UNSIGNED", "Unsigned Number", ""},
		{PROP_FILEPATH, "FILE_PATH", "File Path", ""},
		{PROP_DIRPATH, "DIRECTORY_PATH", "Directory Path", ""},
		{PROP_COLOR, "COLOR", "Color", ""},
		{PROP_VECTOR, "VECTOR", "Vector", ""},
		{PROP_MATRIX, "MATRIX", "Matrix", ""},
		{PROP_ROTATION, "ROTATION", "Rotation", ""},
		{PROP_NEVER_NULL, "NEVER_NULL", "Never Null", ""},
		{PROP_PERCENTAGE, "PERCENTAGE", "Percentage", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "Property", NULL);
	RNA_def_struct_ui_text(srna, "Property Definition", "RNA property definition.");
	RNA_def_struct_refine_func(srna, "rna_Property_refine");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Property_name_get", "rna_Property_name_length", NULL);
	RNA_def_property_ui_text(prop, "Name", "Human readable name.");

	prop= RNA_def_property(srna, "identifier", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Property_identifier_get", "rna_Property_identifier_length", NULL);
	RNA_def_property_ui_text(prop, "Identifier", "Unique name used in the code and scripting.");
	RNA_def_struct_name_property(srna, prop);
		
	prop= RNA_def_property(srna, "description", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Property_description_get", "rna_Property_description_length", NULL);
	RNA_def_property_ui_text(prop, "Description", "Description of the property for tooltips.");

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_enum_funcs(prop, "rna_Property_type_get", NULL);
	RNA_def_property_ui_text(prop, "Type", "Data type of the property.");

	prop= RNA_def_property(srna, "subtype", PROP_ENUM, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_enum_items(prop, subtype_items);
	RNA_def_property_enum_funcs(prop, "rna_Property_subtype_get", NULL);
	RNA_def_property_ui_text(prop, "Subtype", "Semantic interpretation of the property.");

	prop= RNA_def_property(srna, "editable", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_boolean_funcs(prop, "rna_Property_editable_get", NULL);
	RNA_def_property_ui_text(prop, "Editable", "Property is editable through RNA.");
}

static void rna_def_number_property(StructRNA *srna, PropertyType type)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "array_length", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_int_funcs(prop, "rna_Property_array_length_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Array Length", "Maximum length of the array, 0 means unlimited.");

	if(type == PROP_BOOLEAN)
		return;

	prop= RNA_def_property(srna, "hard_min", type, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	if(type == PROP_INT) RNA_def_property_int_funcs(prop, "rna_IntProperty_hard_min_get", NULL, NULL);
	else RNA_def_property_float_funcs(prop, "rna_FloatProperty_hard_min_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Hard Minimum", "Minimum value used by buttons.");

	prop= RNA_def_property(srna, "hard_max", type, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	if(type == PROP_INT) RNA_def_property_int_funcs(prop, "rna_IntProperty_hard_max_get", NULL, NULL);
	else RNA_def_property_float_funcs(prop, "rna_FloatProperty_hard_max_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Hard Maximum", "Maximum value used by buttons.");

	prop= RNA_def_property(srna, "soft_min", type, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	if(type == PROP_INT) RNA_def_property_int_funcs(prop, "rna_IntProperty_soft_min_get", NULL, NULL);
	else RNA_def_property_float_funcs(prop, "rna_FloatProperty_soft_min_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Soft Minimum", "Minimum value used by buttons.");

	prop= RNA_def_property(srna, "soft_max", type, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	if(type == PROP_INT) RNA_def_property_int_funcs(prop, "rna_IntProperty_soft_max_get", NULL, NULL);
	else RNA_def_property_float_funcs(prop, "rna_FloatProperty_soft_max_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Soft Maximum", "Maximum value used by buttons.");

	prop= RNA_def_property(srna, "step", type, PROP_UNSIGNED);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	if(type == PROP_INT) RNA_def_property_int_funcs(prop, "rna_IntProperty_step_get", NULL, NULL);
	else RNA_def_property_float_funcs(prop, "rna_FloatProperty_step_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Step", "Step size used by number buttons, for floats 1/100th of the step size.");

	if(type == PROP_FLOAT) {
		prop= RNA_def_property(srna, "precision", PROP_INT, PROP_UNSIGNED);
		RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
		RNA_def_property_int_funcs(prop, "rna_FloatProperty_precision_get", NULL, NULL);
		RNA_def_property_ui_text(prop, "Precision", "Number of digits after the dot used by buttons.");
	}
}

static void rna_def_string_property(StructRNA *srna)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "max_length", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_int_funcs(prop, "rna_StringProperty_max_length_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Maximum Length", "Maximum length of the string, 0 means unlimited.");
}

static void rna_def_enum_property(BlenderRNA *brna, StructRNA *srna)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "items", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "EnumPropertyItem");
	RNA_def_property_collection_funcs(prop, "rna_EnumProperty_items_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", 0, 0, 0);
	RNA_def_property_ui_text(prop, "Items", "Possible values for the property.");

	srna= RNA_def_struct(brna, "EnumPropertyItem", NULL);
	RNA_def_struct_ui_text(srna, "Enum Item Definition", "Definition of a choice in an RNA enum property.");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_EnumPropertyItem_name_get", "rna_EnumPropertyItem_name_length", NULL);
	RNA_def_property_ui_text(prop, "Name", "Human readable name.");

	prop= RNA_def_property(srna, "identifier", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_EnumPropertyItem_identifier_get", "rna_EnumPropertyItem_identifier_length", NULL);
	RNA_def_property_ui_text(prop, "Identifier", "Unique name used in the code and scripting.");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "value", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_int_funcs(prop, "rna_EnumPropertyItem_value_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Value", "Value of the item.");
}

static void rna_def_pointer_property(StructRNA *srna, PropertyType type)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "fixed_type", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "Struct");
	if(type == PROP_POINTER)
		RNA_def_property_pointer_funcs(prop, "rna_PointerProperty_fixed_type_get", NULL);
	else
		RNA_def_property_pointer_funcs(prop, "rna_CollectionProperty_fixed_type_get", NULL);
	RNA_def_property_ui_text(prop, "Pointer Type", "Fixed pointer type, empty if variable type.");
}

void RNA_def_rna(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* Struct*/
	rna_def_struct(brna);

	/* Property */
	rna_def_property(brna);

	/* BooleanProperty */
	srna= RNA_def_struct(brna, "BooleanProperty", "Property");
	RNA_def_struct_ui_text(srna, "Boolean Definition", "RNA boolean property definition.");
	rna_def_number_property(srna, PROP_BOOLEAN);

	/* IntProperty */
	srna= RNA_def_struct(brna, "IntProperty", "Property");
	RNA_def_struct_ui_text(srna, "Int Definition", "RNA integer number property definition.");
	rna_def_number_property(srna, PROP_INT);

	/* FloatProperty */
	srna= RNA_def_struct(brna, "FloatProperty", "Property");
	RNA_def_struct_ui_text(srna, "Float Definition", "RNA floating pointer number property definition.");
	rna_def_number_property(srna, PROP_FLOAT);

	/* StringProperty */
	srna= RNA_def_struct(brna, "StringProperty", "Property");
	RNA_def_struct_ui_text(srna, "String Definition", "RNA text string property definition.");
	rna_def_string_property(srna);

	/* EnumProperty */
	srna= RNA_def_struct(brna, "EnumProperty", "Property");
	RNA_def_struct_ui_text(srna, "Enum Definition", "RNA enumeration property definition, to choose from a number of predefined options.");
	rna_def_enum_property(brna, srna);

	/* PointerProperty */
	srna= RNA_def_struct(brna, "PointerProperty", "Property");
	RNA_def_struct_ui_text(srna, "Pointer Definition", "RNA pointer property to point to another RNA struct.");
	rna_def_pointer_property(srna, PROP_POINTER);

	/* CollectionProperty */
	srna= RNA_def_struct(brna, "CollectionProperty", "Property");
	RNA_def_struct_ui_text(srna, "Collection Definition", "RNA collection property to define lists, arrays and mappings.");
	rna_def_pointer_property(srna, PROP_COLLECTION);

	/* Blender RNA */
	srna= RNA_def_struct(brna, "BlenderRNA", NULL);
	RNA_def_struct_ui_text(srna, "Blender RNA", "Blender RNA structure definitions.");

	prop= RNA_def_property(srna, "structs", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_struct_type(prop, "Struct");
	RNA_def_property_collection_funcs(prop, "rna_BlenderRNA_structs_begin", "rna_iterator_listbase_next", "rna_iterator_listbase_end", "rna_iterator_listbase_get", 0, 0, 0);
	RNA_def_property_ui_text(prop, "Structs", "");
}

#endif

