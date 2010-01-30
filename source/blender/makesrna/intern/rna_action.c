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
 * Contributor(s): Blender Foundation (2008), Roland Hess, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "WM_types.h"


#ifdef RNA_RUNTIME

static void rna_ActionGroup_channels_next(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;
	FCurve *fcu= (FCurve*)internal->link;
	bActionGroup *grp= fcu->grp;
	
	/* only continue if the next F-Curve (if existant) belongs in the same group */
	if ((fcu->next) && (fcu->next->grp == grp))
		internal->link= (Link*)fcu->next;
	else
		internal->link= NULL;
		
	iter->valid= (internal->link != NULL);
}

#else

static void rna_def_dopesheet(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "DopeSheet", NULL);
	RNA_def_struct_sdna(srna, "bDopeSheet");
	RNA_def_struct_ui_text(srna, "DopeSheet", "Settings for filtering the channels shown in Animation Editors.");
	
	/* Source of DopeSheet data */
	prop= RNA_def_property(srna, "source", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ID");
	RNA_def_property_ui_text(prop, "Source", "ID-Block representing source data, currently ID_SCE (for Dopesheet), and ID_SC (for Grease Pencil).");
	
	/* General Filtering Settings */
	prop= RNA_def_property(srna, "only_selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filterflag", ADS_FILTER_ONLYSEL);
	RNA_def_property_ui_text(prop, "Only Selected", "Only include channels relating to selected objects and data.");
	RNA_def_property_ui_icon(prop, ICON_RESTRICT_SELECT_OFF, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	/* Object Group Filtering Settings */
	prop= RNA_def_property(srna, "only_group_objects", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filterflag", ADS_FILTER_ONLYOBGROUP);
	RNA_def_property_ui_text(prop, "Only Objects in Group", "Only include channels from Objects in the specified Group.");
	RNA_def_property_ui_icon(prop, ICON_GROUP, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "filtering_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "filter_grp");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Filtering Group", "Group that included Object should be a member of.");
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	/* NLA Specific Settings */
	prop= RNA_def_property(srna, "include_missing_nla", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NLA_NOACT);
	RNA_def_property_ui_text(prop, "Include Missing NLA", "Include Animation Data blocks with no NLA data. (NLA Editor only)");
	RNA_def_property_ui_icon(prop, ICON_ACTION, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	/* Summary Settings (DopeSheet editors only) */
	prop= RNA_def_property(srna, "display_summary", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "filterflag", ADS_FILTER_SUMMARY);
	RNA_def_property_ui_text(prop, "Display Summary", "Display an additional 'summary' line. (DopeSheet Editors only)");
	RNA_def_property_ui_icon(prop, ICON_BORDERMOVE, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "collapse_summary", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ADS_FLAG_SUMMARY_COLLAPSED);
	RNA_def_property_ui_text(prop, "Collapse Summary", "Collapse summary when shown, so all other channels get hidden. (DopeSheet Editors Only)");
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	
	/* General DataType Filtering Settings */
	prop= RNA_def_property(srna, "display_shapekeys", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOSHAPEKEYS);
	RNA_def_property_ui_text(prop, "Display Shapekeys", "Include visualization of ShapeKey related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_SHAPEKEY_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_mesh", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOMESH);
	RNA_def_property_ui_text(prop, "Display Meshes", "Include visualization of Mesh related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_MESH_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_camera", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOCAM);
	RNA_def_property_ui_text(prop, "Display Camera", "Include visualization of Camera related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_CAMERA_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_material", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOMAT);
	RNA_def_property_ui_text(prop, "Display Material", "Include visualization of Material related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_MATERIAL_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_lamp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOLAM);
	RNA_def_property_ui_text(prop, "Display Lamp", "Include visualization of Lamp related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_LAMP_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_curve", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOCUR);
	RNA_def_property_ui_text(prop, "Display Curve", "Include visualization of Curve related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_CURVE_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_world", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOWOR);
	RNA_def_property_ui_text(prop, "Display World", "Include visualization of World related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_WORLD_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_scene", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOSCE);
	RNA_def_property_ui_text(prop, "Display Scene", "Include visualization of Scene related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_SCENE_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_particle", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOPART);
	RNA_def_property_ui_text(prop, "Display Particle", "Include visualization of Particle related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_PARTICLE_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_metaball", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOMBA);
	RNA_def_property_ui_text(prop, "Display Metaball", "Include visualization of Metaball related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_META_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_armature", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NOARM);
	RNA_def_property_ui_text(prop, "Display Armature", "Include visualization of Armature related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_ARMATURE_DATA, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
	
	prop= RNA_def_property(srna, "display_node", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "filterflag", ADS_FILTER_NONTREE);
	RNA_def_property_ui_text(prop, "Display Node", "Include visualization of Node related Animation data.");
	RNA_def_property_ui_icon(prop, ICON_NODETREE, 0);
	RNA_def_property_update(prop, NC_ANIMATION|ND_ANIMCHAN_EDIT, NULL);
}

static void rna_def_action_group(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "ActionGroup", NULL);
	RNA_def_struct_sdna(srna, "bActionGroup");
	RNA_def_struct_ui_text(srna, "Action Group", "Groups of F-Curves.");
	
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_struct_name_property(srna, prop);
	
	/* WARNING: be very careful when working with this list, since the endpoint is not
	 * defined like a standard ListBase. Adding/removing channels from this list needs
	 * extreme care, otherwise the F-Curve list running through adjacent groups does
	 * not match up with the one stored in the Action, resulting in curves which do not
	 * show up in animation editors. For that reason, such operations are currently 
	 * prohibited.
	 */
	prop= RNA_def_property(srna, "channels", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "channels", NULL);
	RNA_def_property_struct_type(prop, "FCurve");
	RNA_def_property_collection_funcs(prop, 0, "rna_ActionGroup_channels_next", 0, 0, 0, 0, 0);
	RNA_def_property_ui_text(prop, "Channels", "F-Curves in this group.");
	
	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", AGRP_SELECTED);
	RNA_def_property_ui_text(prop, "Selected", "Action Group is selected.");
	
	prop= RNA_def_property(srna, "locked", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", AGRP_PROTECTED);
	RNA_def_property_ui_text(prop, "Locked", "Action Group is locked.");
	
	prop= RNA_def_property(srna, "expanded", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", AGRP_EXPANDED);
	RNA_def_property_ui_text(prop, "Expanded", "Action Group is expanded.");
	
	prop= RNA_def_property(srna, "custom_color", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "customCol");
	RNA_def_property_ui_text(prop, "Custom Color", "Index of custom color set.");
}

static void rna_def_action(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Action", "ID");
	RNA_def_struct_sdna(srna, "bAction");
	RNA_def_struct_ui_text(srna, "Action", "A collection of F-Curves for animation.");
	RNA_def_struct_ui_icon(srna, ICON_ACTION);

	prop= RNA_def_property(srna, "fcurves", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "curves", NULL);
	RNA_def_property_struct_type(prop, "FCurve");
	RNA_def_property_ui_text(prop, "F-Curves", "The individual F-Curves that make up the Action.");

	prop= RNA_def_property(srna, "groups", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "groups", NULL);
	RNA_def_property_struct_type(prop, "ActionGroup");
	RNA_def_property_ui_text(prop, "Groups", "Convenient groupings of F-Curves.");

	prop= RNA_def_property(srna, "pose_markers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "markers", NULL);
	RNA_def_property_struct_type(prop, "TimelineMarker");
	RNA_def_property_ui_text(prop, "Pose Markers", "Markers specific to this Action, for labeling poses.");

	RNA_api_action(srna);
}

/* --------- */

void RNA_def_action(BlenderRNA *brna)
{
	rna_def_action(brna);
	rna_def_action_group(brna);
	rna_def_dopesheet(brna);
}


#endif
