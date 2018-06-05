/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/makesrna/intern/rna_group.c
 *  \ingroup RNA
 */

#include <stdlib.h>

#include "DNA_group_types.h"

#include "BLI_utildefines.h"

#include "RNA_define.h"

#include "rna_internal.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"

#include "BKE_collection.h"
#include "BKE_layer.h"

#include "WM_api.h"

static void rna_Collection_all_objects_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Collection *collection = (Collection *)ptr->data;
	ListBase collection_objects = BKE_collection_object_cache_get(collection);
	rna_iterator_listbase_begin(iter, &collection_objects, NULL);
}

static PointerRNA rna_Collection_all_objects_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal = &iter->internal.listbase;

	/* we are actually iterating a ObjectBase list, so override get */
	Base *base = (Base *)internal->link;
	return rna_pointer_inherit_refine(&iter->parent, &RNA_Object, base->object);
}

static void rna_Collection_objects_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Collection *collection = (Collection *)ptr->data;
	rna_iterator_listbase_begin(iter, &collection->gobject, NULL);
}

static PointerRNA rna_Collection_objects_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal = &iter->internal.listbase;

	/* we are actually iterating a ObjectBase list, so override get */
	CollectionObject *cob = (CollectionObject *)internal->link;
	return rna_pointer_inherit_refine(&iter->parent, &RNA_Object, cob->ob);
}

static void rna_Collection_objects_link(Collection *collection, Main *bmain, ReportList *reports, Object *object)
{
	if (!BKE_collection_object_add(bmain, collection, object)) {
		BKE_reportf(reports, RPT_ERROR, "Object '%s' already in collection '%s'", object->id.name + 2, collection->id.name + 2);
		return;
	}

	DEG_relations_tag_update(bmain);
	WM_main_add_notifier(NC_OBJECT | ND_DRAW, &object->id);
}

static void rna_Collection_objects_unlink(Collection *collection, Main *bmain, ReportList *reports, Object *object)
{
	if (!BKE_collection_object_remove(bmain, collection, object, false)) {
		BKE_reportf(reports, RPT_ERROR, "Object '%s' not in collection '%s'", object->id.name + 2, collection->id.name + 2);
		return;
	}

	DEG_relations_tag_update(bmain);
	WM_main_add_notifier(NC_OBJECT | ND_DRAW, &object->id);
}

static void rna_Collection_children_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Collection *collection = (Collection *)ptr->data;
	rna_iterator_listbase_begin(iter, &collection->children, NULL);
}

static PointerRNA rna_Collection_children_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal = &iter->internal.listbase;

	/* we are actually iterating a CollectionBase list, so override get */
	CollectionChild *child = (CollectionChild *)internal->link;
	return rna_pointer_inherit_refine(&iter->parent, &RNA_Collection, child->collection);
}

static void rna_Collection_children_link(Collection *collection, Main *bmain, ReportList *reports, Collection *child)
{
	if (!BKE_collection_child_add(bmain, collection, child)) {
		BKE_reportf(reports, RPT_ERROR, "Collection '%s' already in collection '%s'", child->id.name + 2, collection->id.name + 2);
		return;
	}

	DEG_relations_tag_update(bmain);
	WM_main_add_notifier(NC_OBJECT | ND_DRAW, &child->id);
}

static void rna_Collection_children_unlink(Collection *collection, Main *bmain, ReportList *reports, Collection *child)
{
	if (!BKE_collection_child_remove(bmain, collection, child)) {
		BKE_reportf(reports, RPT_ERROR, "Collection '%s' not in collection '%s'", child->id.name + 2, collection->id.name + 2);
		return;
	}

	DEG_relations_tag_update(bmain);
	WM_main_add_notifier(NC_OBJECT | ND_DRAW, &child->id);
}

static void rna_Collection_flag_update(Main *bmain, Scene *scene, PointerRNA *ptr)
{
	Collection *collection = (Collection *)ptr->data;
	BKE_collection_object_cache_free(collection);
	BKE_main_collection_sync(bmain);

	DEG_relations_tag_update(bmain);
	DEG_id_tag_update(&collection->id, 0);
	WM_main_add_notifier(NC_SCENE | ND_OB_SELECT, scene);
}

#else

/* collection.objects */
static void rna_def_collection_objects(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;
	
	RNA_def_property_srna(cprop, "CollectionObjects");
	srna = RNA_def_struct(brna, "CollectionObjects", NULL);
	RNA_def_struct_sdna(srna, "Collection");
	RNA_def_struct_ui_text(srna, "Collection Objects", "Collection of collection objects");

	/* add object */
	func = RNA_def_function(srna, "link", "rna_Collection_objects_link");
	RNA_def_function_flag(func, FUNC_USE_REPORTS | FUNC_USE_MAIN);
	RNA_def_function_ui_description(func, "Add this object to a collection");
	parm = RNA_def_pointer(func, "object", "Object", "", "Object to add");
	RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);

	/* remove object */
	func = RNA_def_function(srna, "unlink", "rna_Collection_objects_unlink");
	RNA_def_function_ui_description(func, "Remove this object from a collection");
	RNA_def_function_flag(func, FUNC_USE_REPORTS | FUNC_USE_MAIN);
	parm = RNA_def_pointer(func, "object", "Object", "", "Object to remove");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
}

/* collection.children */
static void rna_def_collection_children(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "CollectionChildren");
	srna = RNA_def_struct(brna, "CollectionChildren", NULL);
	RNA_def_struct_sdna(srna, "Collection");
	RNA_def_struct_ui_text(srna, "Collection Children", "Collection of child collections");

	/* add child */
	func = RNA_def_function(srna, "link", "rna_Collection_children_link");
	RNA_def_function_flag(func, FUNC_USE_REPORTS | FUNC_USE_MAIN);
	RNA_def_function_ui_description(func, "Add this collection as child of this collection");
	parm = RNA_def_pointer(func, "child", "Collection", "", "Collection to add");
	RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);

	/* remove child */
	func = RNA_def_function(srna, "unlink", "rna_Collection_children_unlink");
	RNA_def_function_ui_description(func, "Remove this child collection from a collection");
	RNA_def_function_flag(func, FUNC_USE_REPORTS | FUNC_USE_MAIN);
	parm = RNA_def_pointer(func, "child", "Collection", "", "Collection to remove");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
}


void RNA_def_collections(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "Collection", "ID");
	RNA_def_struct_sdna(srna, "Group"); /* it is actually Collection but for 2.8 the dna is patched! */
	RNA_def_struct_ui_text(srna, "Collection", "Collection of Object data-blocks");
	RNA_def_struct_ui_icon(srna, ICON_GROUP);
	/* this is done on save/load in readfile.c, removed if no objects are in the collection and not in a scene */
	RNA_def_struct_clear_flag(srna, STRUCT_ID_REFCOUNT);

	prop = RNA_def_property(srna, "dupli_offset", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_float_sdna(prop, NULL, "dupli_ofs");
	RNA_def_property_ui_text(prop, "Dupli Offset", "Offset from the origin to use when instancing");
	RNA_def_property_ui_range(prop, -10000.0, 10000.0, 10, RNA_TRANSLATION_PREC_DEFAULT);
	RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, NULL);

	prop = RNA_def_property(srna, "objects", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_STATIC);
	RNA_def_property_ui_text(prop, "Objects", "Objects that are directly in this collection");
	RNA_def_property_collection_funcs(prop, "rna_Collection_objects_begin",
	                                        "rna_iterator_listbase_next",
	                                        "rna_iterator_listbase_end",
	                                        "rna_Collection_objects_get",
	                                        NULL, NULL, NULL, NULL);
	rna_def_collection_objects(brna, prop);

	prop = RNA_def_property(srna, "all_objects", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "All Objects", "Objects that are in this collection and its child collections");
	RNA_def_property_collection_funcs(prop, "rna_Collection_all_objects_begin",
	                                        "rna_iterator_listbase_next",
	                                        "rna_iterator_listbase_end",
	                                        "rna_Collection_all_objects_get",
	                                        NULL, NULL, NULL, NULL);

	prop = RNA_def_property(srna, "children", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Collection");
	RNA_def_property_ui_text(prop, "Children", "Collections that are immediate children of this collection");
	RNA_def_property_collection_funcs(prop, "rna_Collection_children_begin",
	                                        "rna_iterator_listbase_next",
	                                        "rna_iterator_listbase_end",
	                                        "rna_Collection_children_get",
	                                        NULL, NULL, NULL, NULL);
	rna_def_collection_children(brna, prop);

	/* Flags */
	prop = RNA_def_property(srna, "hide_select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", COLLECTION_RESTRICT_SELECT);
	RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_STATIC);
	RNA_def_property_ui_icon(prop, ICON_RESTRICT_SELECT_OFF, 1);
	RNA_def_property_ui_text(prop, "Restrict Select", "Disable collection object selection in the 3D viewport");
	RNA_def_property_update(prop, NC_SCENE | ND_LAYER_CONTENT, "rna_Collection_flag_update");

	prop = RNA_def_property(srna, "hide_viewport", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", COLLECTION_RESTRICT_VIEW);
	RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_STATIC);
	RNA_def_property_ui_icon(prop, ICON_RESTRICT_VIEW_OFF, 1);
	RNA_def_property_ui_text(prop, "Restrict Viewport", "Hide collection objects in the 3D viewport");
	RNA_def_property_update(prop, NC_SCENE | ND_LAYER_CONTENT, "rna_Collection_flag_update");

	prop = RNA_def_property(srna, "hide_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", COLLECTION_RESTRICT_RENDER);
	RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_STATIC);
	RNA_def_property_ui_icon(prop, ICON_RESTRICT_RENDER_OFF, 1);
	RNA_def_property_ui_text(prop, "Restrict Render", "Hide collection objects in renders");
	RNA_def_property_update(prop, NC_SCENE | ND_LAYER_CONTENT, "rna_Collection_flag_update");
}

#endif
