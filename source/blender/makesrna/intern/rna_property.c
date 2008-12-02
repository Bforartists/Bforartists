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

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_property_types.h"

#ifdef RNA_RUNTIME

static StructRNA* rna_GameProperty_refine(struct PointerRNA *ptr)
{
	bProperty *property= (bProperty*)ptr->data;

	switch(property->type){
		case PROP_BOOL:
			return &RNA_GameBooleanProperty;
		case PROP_INT:
			return &RNA_GameIntProperty;
		case PROP_FLOAT:
			return &RNA_GameFloatProperty;
		case PROP_STRING:
			return &RNA_GameStringProperty;
		case PROP_TIME:
			return &RNA_GameTimeProperty;
		default:
			return &RNA_GameProperty;
	}
}

/* for both float and timer */
static float rna_GameFloatProperty_value_get(PointerRNA *ptr)
{
	bProperty *prop= (bProperty*)(ptr->data);
	return *(float*)(&prop->data);
}

static void rna_GameFloatProperty_value_set(PointerRNA *ptr, float value)
{
	bProperty *prop= (bProperty*)(ptr->data);
	CLAMP(value, -10000.0f, 10000.0f);
	*(float*)(&prop->data)= value;
}

#else

void RNA_def_gameproperty(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem gameproperty_type_items[] ={
		{PROP_BOOL, "BOOL", "Boolean", ""},
		{PROP_INT, "INT", "Integer", ""},
		{PROP_FLOAT, "FLOAT", "Float", ""},
		{PROP_STRING, "STRING", "String", ""},
		{PROP_TIME, "TIME", "Time", ""},
		{0, NULL, NULL, NULL}};

	/* Base Struct for GameProperty */
	srna= RNA_def_struct(brna, "GameProperty", NULL , "Game Property");
	RNA_def_struct_sdna(srna, "bProperty");
	RNA_def_struct_funcs(srna, NULL, "rna_GameProperty_refine");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE); /* must be unique */
	RNA_def_property_ui_text(prop, "Name", "Available as as GameObject attributes in the game engines python api");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_enum_items(prop, gameproperty_type_items);
	RNA_def_property_ui_text(prop, "Type", "");

	prop= RNA_def_property(srna, "debug", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PROP_DEBUG);
	RNA_def_property_ui_text(prop, "Debug", "Print debug information for this property.");

	/* GameBooleanProperty */
	srna= RNA_def_struct(brna, "GameBooleanProperty", "GameProperty" , "Game Boolean Property");
	RNA_def_struct_sdna(srna, "bProperty");

	prop= RNA_def_property(srna, "boolean_value", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "data", 1);
	RNA_def_property_ui_text(prop, "Value", "Property value.");

	/* GameIntProperty */
	srna= RNA_def_struct(brna, "GameIntProperty", "GameProperty" , "Game Integer Property");
	RNA_def_struct_sdna(srna, "bProperty");

	prop= RNA_def_property(srna, "value", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "data");
	RNA_def_property_ui_text(prop, "Value", "Property value.");
	RNA_def_property_range(prop, -10000, 10000);

	/* GameFloatProperty */
	srna= RNA_def_struct(brna, "GameFloatProperty", "GameProperty" , "Game Float Property");
	RNA_def_struct_sdna(srna, "bProperty");

	prop= RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "data");
	RNA_def_property_ui_text(prop, "Value", "Property value.");
	RNA_def_property_range(prop, -10000, 10000);
	RNA_def_property_float_funcs(prop, "rna_GameFloatProperty_value_get", "rna_GameFloatProperty_value_set", NULL);

	/* GameTimerProperty */
	srna= RNA_def_struct(brna, "GameTimeProperty", "GameProperty" , "Game Time Property");
	RNA_def_struct_sdna(srna, "bProperty");

	prop= RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "data");
	RNA_def_property_ui_text(prop, "Value", "Property value.");
	RNA_def_property_range(prop, -10000, 10000);
	RNA_def_property_float_funcs(prop, "rna_GameFloatProperty_value_get", "rna_GameFloatProperty_value_set", NULL);

	/* GameStringProperty */
	srna= RNA_def_struct(brna, "GameStringProperty", "GameProperty" , "Game String Property");
	RNA_def_struct_sdna(srna, "bProperty");

	prop= RNA_def_property(srna, "value", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "poin");
	RNA_def_property_string_maxlength(prop, MAX_PROPSTRING);
	RNA_def_property_ui_text(prop, "Value", "Property value.");
}

#endif

