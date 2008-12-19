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
#include <stdio.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "DNA_ID.h"

#ifdef RNA_RUNTIME

#include "BKE_idprop.h"

/* name functions that ignore the first two ID characters */
static void rna_ID_name_get(PointerRNA *ptr, char *value)
{
	ID *id= (ID*)ptr->data;
	BLI_strncpy(value, id->name+2, sizeof(id->name)-2);
}

static int rna_ID_name_length(PointerRNA *ptr)
{
	ID *id= (ID*)ptr->data;
	return strlen(id->name+2);
}

static void rna_ID_name_set(PointerRNA *ptr, const char *value)
{
	ID *id= (ID*)ptr->data;
	BLI_strncpy(id->name+2, value, sizeof(id->name)-2);
}

static StructRNA *rna_ID_refine(PointerRNA *ptr)
{
	ID *id= (ID*)ptr->data;

	switch(GS(id->name)) {
		case ID_AR: return &RNA_Armature;
		case ID_BR: return &RNA_Brush;
		case ID_CA: return &RNA_Camera;
		case ID_CU: return &RNA_Curve;
		case ID_GR: return &RNA_Group;
		case ID_IM: return &RNA_Image;
		case ID_IP: return &RNA_Ipo;
		case ID_KE: return &RNA_Key;
		case ID_LA: return &RNA_Lamp;
		case ID_LI: return &RNA_Library;
		case ID_LT: return &RNA_Lattice;
		case ID_MA: return &RNA_Material;
		case ID_MB: return &RNA_MetaBall;
		case ID_NT: return &RNA_NodeTree;
		case ID_ME: return &RNA_Mesh;
		case ID_OB: return &RNA_Object;
		case ID_SCE: return &RNA_Scene;
		case ID_SCR: return &RNA_Screen;
		case ID_VF: return &RNA_VectorFont;
		case ID_WO: return &RNA_World;
		case ID_WM: return &RNA_WindowManager;
		default: return &RNA_ID;
	}
}

static void rna_ID_fake_user_set(PointerRNA *ptr, int value)
{
	ID *id= (ID*)ptr->data;

	if(value && !(id->flag & LIB_FAKEUSER)) {
		id->flag |= LIB_FAKEUSER;
		id->us++;
	}
	else if(!value && (id->flag & LIB_FAKEUSER)) {
		id->flag &= ~LIB_FAKEUSER;
		id->us--;
	}
}

#else

static void rna_def_ID_properties(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* this is struct is used for holding the virtual
	 * PropertyRNA's for ID properties */
	srna= RNA_def_struct(brna, "IDProperty", NULL);
	RNA_def_struct_ui_text(srna, "ID Property", "stores arbitrary properties");
	

	/* IDP_STRING */
	prop= RNA_def_property(srna, "string", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);

	/* IDP_INT */
	prop= RNA_def_property(srna, "int", PROP_INT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);

	prop= RNA_def_property(srna, "intarray", PROP_INT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);
	RNA_def_property_array(prop, 1);

	/* IDP_FLOAT */
	prop= RNA_def_property(srna, "float", PROP_FLOAT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);

	prop= RNA_def_property(srna, "floatarray", PROP_FLOAT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);
	RNA_def_property_array(prop, 1);

	/* IDP_DOUBLE */
	prop= RNA_def_property(srna, "double", PROP_FLOAT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);

	prop= RNA_def_property(srna, "doublearray", PROP_FLOAT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_IDPROPERTY);
	RNA_def_property_array(prop, 1);

	/* IDP_GROUP */
	prop= RNA_def_property(srna, "group", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_EXPORT|PROP_NOT_EDITABLE|PROP_IDPROPERTY);
	RNA_def_property_struct_type(prop, "IDPropertyGroup");

	/* IDP_ID -- not implemented yet in id properties */

	/* ID property groups > level 0, since level 0 group is merged
	 * with native RNA properties. the builtin_properties will take
	 * care of the properties here */
	srna= RNA_def_struct(brna, "IDPropertyGroup", NULL);
	RNA_def_struct_ui_text(srna, "ID Property Group", "a collection of properties");
}

static void rna_def_ID(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ID", NULL);
	RNA_def_struct_ui_text(srna, "ID", "Used as a basis for dealing with many types with unique names, garbage collection and linked libraries");
	
	RNA_def_struct_flag(srna, STRUCT_ID);
	RNA_def_struct_funcs(srna, NULL, "rna_ID_refine");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE); /* must be unique */
	RNA_def_property_ui_text(prop, "Name", "Unique datablock ID name.");
	RNA_def_property_string_funcs(prop, "rna_ID_name_get", "rna_ID_name_length", "rna_ID_name_set");
	RNA_def_property_string_maxlength(prop, sizeof(((ID*)NULL)->name)-2);
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "users", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "us");
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_ui_text(prop, "Users", "Number of times this datablock is referenced.");

	prop= RNA_def_property(srna, "fake_user", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIB_FAKEUSER);
	RNA_def_property_ui_text(prop, "Fake User", "Saves this datablock even if it has no users");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_ID_fake_user_set");

	prop= RNA_def_property(srna, "library", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "lib");
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_ui_text(prop, "Library", "Library file the datablock is linked from.");
}

static void rna_def_library(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Library", "ID");
	RNA_def_struct_ui_text(srna, "Library", "reference to an external blend file");

	prop= RNA_def_property(srna, "filename", PROP_STRING, PROP_FILEPATH);
	RNA_def_property_string_sdna(prop, NULL, "name");
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_ui_text(prop, "Filename", "Path to the library .blend file.");
}
void RNA_def_ID(BlenderRNA *brna)
{
	StructRNA *srna;
	/* simple built-in unknown type */
	srna= RNA_def_struct(brna, "UnknownType", NULL);
	RNA_def_struct_ui_text(srna, "Unknown Type", "");
	

	rna_def_ID(brna);
	rna_def_ID_properties(brna);
	rna_def_library(brna);
}

#endif

