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

#ifdef RNA_RUNTIME

#include "BKE_global.h"

void *rna_Scene_objects_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;

	/* we are actually iterating a Base list, so override get */
	return ((Base*)internal->link)->object;
}

static void rna_Scene_layer_set(PointerRNA *ptr, int index, int value)
{
	Scene *scene= (Scene*)ptr->data;

	if(value) scene->lay |= (1<<index);
	else {
		scene->lay &= ~(1<<index);
		if(scene->lay == 0)
			scene->lay |= (1<<index);
	}
}

#else

void RNA_def_scene(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	static EnumPropertyItem prop_mode_items[] = {{PROP_SMOOTH, "SMOOTH", "Smooth"}, {PROP_SPHERE, "SPHERE", "Sphere"}, {PROP_ROOT, "ROOT", "Root"}, {PROP_SHARP, "SHARP", "Sharp"}, {PROP_LIN, "LINEAR", "Linear"}, {PROP_CONST, "CONSTANT", "Constant"}, {PROP_RANDOM, "RANDOM", "Random"}, {0, NULL, NULL}};
	static EnumPropertyItem unwrapper_items[] = {{0, "CONFORMAL", "Conformal"}, {1, "ANGLEBASED", "Angle Based"},  {0, NULL, NULL}};
	
	srna= RNA_def_struct(brna, "Scene", "Scene");

	RNA_def_ID(srna);

	prop= RNA_def_property(srna, "camera", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Active Camera", "Active camera used for rendering the scene.");

	prop= RNA_def_property(srna, "cursor", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_ui_text(prop, "Cursor Location", "3D cursor location.");
	RNA_def_property_ui_range(prop, -10000.0, 10000.0, 10, 4);

	prop= RNA_def_property(srna, "objects", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "base", NULL);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Objects", "Objects in the scene.");
	RNA_def_property_collection_funcs(prop, 0, 0, 0, "rna_Scene_objects_get", 0, 0, 0, 0);

	prop= RNA_def_property(srna, "layer", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "lay", 1);
	RNA_def_property_array(prop, 20);
	RNA_def_property_ui_text(prop, "Visible Layers", "Layers visible when rendering the scene.");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_Scene_layer_set");

	prop= RNA_def_property(srna, "prop_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Proportional Mode", "Proportional edit mode.");

	prop= RNA_def_property(srna, "current_frame", PROP_INT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_DRIVEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.cfra");
	RNA_def_property_range(prop, MINFRAME, MAXFRAME);
	RNA_def_property_ui_text(prop, "Current Frame", "Current frame.");

	prop= RNA_def_property(srna, "stamp_note", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "r.stamp_udata");
	RNA_def_property_ui_text(prop, "Stamp Note", "User define note for the render stamping.");

	prop= RNA_def_property(srna, "unwrapper", PROP_ENUM, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "toolsettings->unwrapper");
	RNA_def_property_enum_items(prop, unwrapper_items);
	RNA_def_property_ui_text(prop, "Unwrapper", "Unwrap algorithm used by the Unwrap tool.");
}

#endif

