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
 * The Original Code is Copyright (C) Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/object/object_group.c
 *  \ingroup edobj
 */


#include <string.h>

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "DNA_group_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_group.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_object.h"

#include "ED_screen.h"
#include "ED_object.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "object_intern.h"

/********************* 3d view operators ***********************/

/* can be called with C == NULL */
static EnumPropertyItem *group_object_active_itemf(bContext *C, PointerRNA *UNUSED(ptr), PropertyRNA *UNUSED(prop), int *free)
{
	Object *ob;
	EnumPropertyItem *item = NULL, item_tmp = {0};
	int totitem = 0;

	if (C == NULL) {
		return DummyRNA_NULL_items;
	}

	ob = ED_object_context(C);

	/* check that the action exists */
	if (ob) {
		Group *group = NULL;
		int i = 0;

		while ((group = find_group(ob, group))) {
			item_tmp.identifier = item_tmp.name = group->id.name + 2;
			/* item_tmp.icon = ICON_ARMATURE_DATA; */
			item_tmp.value = i;
			RNA_enum_item_add(&item, &totitem, &item_tmp);
			i++;
		}
	}

	RNA_enum_item_end(&item, &totitem);
	*free = 1;

	return item;
}

/* get the group back from the enum index, quite awkward and UI specific */
static Group *group_object_active_find_index(Object *ob, const int group_object_index)
{
	Group *group = NULL;
	int i = 0;
	while ((group = find_group(ob, group))) {
		if (i == group_object_index) {
			break;
		}
		i++;
	}

	return group;
}

static int objects_add_active_exec(bContext *C, wmOperator *op)
{
	Object *ob = ED_object_context(C);
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	int group_object_index = RNA_enum_get(op->ptr, "group");
	int is_cycle = FALSE;

	if (ob) {
		Group *group = group_object_active_find_index(ob, group_object_index);

		/* now add all selected objects from the group */
		if (group) {

			CTX_DATA_BEGIN (C, Base *, base, selected_editable_bases)
			{
				if (base->object->dup_group != group) {
					add_to_group(group, base->object, scene, base);
				}
				else {
					is_cycle = TRUE;
				}
			}
			CTX_DATA_END;

			if (is_cycle) {
				BKE_report(op->reports, RPT_WARNING, "Skipped some groups because of cycle detected");
			}

			DAG_scene_sort(bmain, scene);
			WM_event_add_notifier(C, NC_GROUP | NA_EDITED, NULL);

			return OPERATOR_FINISHED;
		}
	}

	return OPERATOR_CANCELLED;
}

void GROUP_OT_objects_add_active(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Add Selected To Active Group";
	ot->description = "Add the object to an object group that contains the active object";
	ot->idname = "GROUP_OT_objects_add_active";
	
	/* api callbacks */
	ot->exec = objects_add_active_exec;
	ot->invoke = WM_menu_invoke;
	ot->poll = ED_operator_objectmode;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	prop = RNA_def_enum(ot->srna, "group", DummyRNA_NULL_items, 0, "Group", "The group to add other selected objects to");
	RNA_def_enum_funcs(prop, group_object_active_itemf);
	ot->prop = prop;
}

static int objects_remove_active_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	Object *ob = OBACT;
	Group *group;
	int ok = 0;
	
	if (!ob) return OPERATOR_CANCELLED;
	
	/* linking to same group requires its own loop so we can avoid
	 * looking up the active objects groups each time */

	for (group = bmain->group.first; group; group = group->id.next) {
		if (object_in_group(ob, group)) {
			/* Assign groups to selected objects */
			CTX_DATA_BEGIN (C, Base *, base, selected_editable_bases)
			{
				rem_from_group(group, base->object, scene, base);
				ok = 1;
			}
			CTX_DATA_END;
		}
	}
	
	if (!ok) BKE_report(op->reports, RPT_ERROR, "Active Object contains no groups");
	
	DAG_scene_sort(bmain, scene);
	WM_event_add_notifier(C, NC_GROUP | NA_EDITED, NULL);
	
	return OPERATOR_FINISHED;
}

void GROUP_OT_objects_remove_active(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Remove Selected From Active Group";
	ot->description = "Remove the object from an object group that contains the active object";
	ot->idname = "GROUP_OT_objects_remove_active";
	
	/* api callbacks */
	ot->exec = objects_remove_active_exec;	
	ot->poll = ED_operator_objectmode;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int group_objects_remove_all_exec(bContext *C, wmOperator *UNUSED(op))
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);

	CTX_DATA_BEGIN (C, Base *, base, selected_editable_bases)
	{
		BKE_object_groups_clear(scene, base, base->object);
	}
	CTX_DATA_END;

	DAG_scene_sort(bmain, scene);
	WM_event_add_notifier(C, NC_GROUP | NA_EDITED, NULL);
	
	return OPERATOR_FINISHED;
}

void GROUP_OT_objects_remove_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Remove From All Groups";
	ot->description = "Remove selected objects from all groups or a selected group";
	ot->idname = "GROUP_OT_objects_remove_all";
	
	/* api callbacks */
	ot->exec = group_objects_remove_all_exec;
	ot->poll = ED_operator_objectmode;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int group_objects_remove_exec(bContext *C, wmOperator *op)
{
	Object *ob = ED_object_context(C);
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	int group_object_index = RNA_enum_get(op->ptr, "group");

	if (ob) {
		Group *group = group_object_active_find_index(ob, group_object_index);

		/* now remove all selected objects from the group */
		if (group) {

			CTX_DATA_BEGIN (C, Base *, base, selected_editable_bases)
			{
				rem_from_group(group, base->object, scene, base);
			}
			CTX_DATA_END;

			DAG_scene_sort(bmain, scene);
			WM_event_add_notifier(C, NC_GROUP | NA_EDITED, NULL);

			return OPERATOR_FINISHED;
		}
	}

	return OPERATOR_CANCELLED;
}

void GROUP_OT_objects_remove(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Remove From Group";
	ot->description = "Remove selected objects from all groups or a selected group";
	ot->idname = "GROUP_OT_objects_remove";

	/* api callbacks */
	ot->exec = group_objects_remove_exec;
	ot->invoke = WM_menu_invoke;
	ot->poll = ED_operator_objectmode;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	prop = RNA_def_enum(ot->srna, "group", DummyRNA_NULL_items, 0, "Group", "The group to remove this object from");
	RNA_def_enum_funcs(prop, group_object_active_itemf);
	ot->prop = prop;
}

static int group_create_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	Group *group = NULL;
	char name[MAX_ID_NAME - 2]; /* id name */
	
	RNA_string_get(op->ptr, "name", name);
	
	group = add_group(name);
		
	CTX_DATA_BEGIN (C, Base *, base, selected_editable_bases)
	{
		add_to_group(group, base->object, scene, base);
	}
	CTX_DATA_END;

	DAG_scene_sort(bmain, scene);
	WM_event_add_notifier(C, NC_GROUP | NA_EDITED, NULL);
	
	return OPERATOR_FINISHED;
}

void GROUP_OT_create(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Create New Group";
	ot->description = "Create an object group from selected objects";
	ot->idname = "GROUP_OT_create";
	
	/* api callbacks */
	ot->exec = group_create_exec;	
	ot->poll = ED_operator_objectmode;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_string(ot->srna, "name", "Group", MAX_ID_NAME - 2, "Name", "Name of the new group");
}

/****************** properties window operators *********************/

static int group_add_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = ED_object_context(C);
	Group *group;

	if (ob == NULL)
		return OPERATOR_CANCELLED;

	group = add_group("Group");
	add_to_group(group, ob, scene, NULL);

	WM_event_add_notifier(C, NC_OBJECT | ND_DRAW, ob);

	return OPERATOR_FINISHED;
}

void OBJECT_OT_group_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Add to Group";
	ot->idname = "OBJECT_OT_group_add";
	ot->description = "Add an object to a new group";
	
	/* api callbacks */
	ot->exec = group_add_exec;
	ot->poll = ED_operator_objectmode;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int group_link_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = ED_object_context(C);
	Group *group = BLI_findlink(&CTX_data_main(C)->group, RNA_enum_get(op->ptr, "group"));

	if (ELEM(NULL, ob, group))
		return OPERATOR_CANCELLED;

	add_to_group(group, ob, scene, NULL);

	WM_event_add_notifier(C, NC_OBJECT | ND_DRAW, ob);

	return OPERATOR_FINISHED;
}

void OBJECT_OT_group_link(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Link to Group";
	ot->idname = "OBJECT_OT_group_link";
	ot->description = "Add an object to an existing group";
	
	/* api callbacks */
	ot->exec = group_link_exec;
	ot->invoke = WM_enum_search_invoke;
	ot->poll = ED_operator_objectmode;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	prop = RNA_def_enum(ot->srna, "group", DummyRNA_NULL_items, 0, "Group", "");
	RNA_def_enum_funcs(prop, RNA_group_local_itemf);
	ot->prop = prop;
}

static int group_remove_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = ED_object_context(C);
	Group *group = CTX_data_pointer_get_type(C, "group", &RNA_Group).data;

	if (!ob || !group)
		return OPERATOR_CANCELLED;

	rem_from_group(group, ob, scene, NULL); /* base will be used if found */

	WM_event_add_notifier(C, NC_OBJECT | ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_group_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Remove Group";
	ot->idname = "OBJECT_OT_group_remove";
	ot->description = "Remove the active object from this group";
	
	/* api callbacks */
	ot->exec = group_remove_exec;
	ot->poll = ED_operator_objectmode;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

