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
 * Contributor(s): Daniel Genrich
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <limits.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "BKE_modifier.h"
#include "BKE_smoke.h"

#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_smoke_types.h"

#include "WM_types.h"


#ifdef RNA_RUNTIME

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_particle.h"

#include "ED_object.h"

static void rna_Smoke_update(bContext *C, PointerRNA *ptr)
{
	DAG_object_flush_update(CTX_data_scene(C), ptr->id.data, OB_RECALC_DATA);
}

static void rna_Smoke_dependency_update(bContext *C, PointerRNA *ptr)
{
	rna_Smoke_update(C, ptr);
    DAG_scene_sort(CTX_data_scene(C));
}

static void rna_Smoke_reset(bContext *C, PointerRNA *ptr)
{
	SmokeDomainSettings *settings = (SmokeDomainSettings*)ptr->data;

	smokeModifier_reset(settings->smd);

	rna_Smoke_update(C, ptr);
}

static void rna_Smoke_reset_dependancy(bContext *C, PointerRNA *ptr)
{
	SmokeDomainSettings *settings = (SmokeDomainSettings*)ptr->data;

	smokeModifier_reset(settings->smd);

	rna_Smoke_dependency_update(C, ptr);
}

static void rna_Smoke_redraw(bContext *C, PointerRNA *ptr)
{
	SmokeDomainSettings *settings = (SmokeDomainSettings*)ptr->data;

	settings->flags |= MOD_SMOKE_VIEW_REDRAWNICE;
}

static char *rna_SmokeDomainSettings_path(PointerRNA *ptr)
{
	SmokeDomainSettings *settings = (SmokeDomainSettings*)ptr->data;
	ModifierData *md= (ModifierData *)settings->smd;

	return BLI_sprintfN("modifiers[%s].domain_settings", md->name);
}

static char *rna_SmokeFlowSettings_path(PointerRNA *ptr)
{
	SmokeFlowSettings *settings = (SmokeFlowSettings*)ptr->data;
	ModifierData *md= (ModifierData *)settings->smd;

	return BLI_sprintfN("modifiers[%s].flow_settings", md->name);
}

static char *rna_SmokeCollSettings_path(PointerRNA *ptr)
{
	SmokeCollSettings *settings = (SmokeCollSettings*)ptr->data;
	ModifierData *md= (ModifierData *)settings->smd;

	return BLI_sprintfN("modifiers[%s].coll_settings", md->name);
}

#else

static void rna_def_smoke_domain_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_noise_type_items[] = {
				{MOD_SMOKE_NOISEWAVE, "NOISEWAVE", 0, "Wavelet", ""},
			/*  {MOD_SMOKE_NOISEFFT, "NOISEFFT", 0, "FFT", ""}, */
			/* 	{MOD_SMOKE_NOISECURL, "NOISECURL", 0, "Curl", ""}, */
				{0, NULL, 0, NULL, NULL}};

	srna = RNA_def_struct(brna, "SmokeDomainSettings", NULL);
	RNA_def_struct_ui_text(srna, "Domain Settings", "Smoke domain settings.");
	RNA_def_struct_sdna(srna, "SmokeDomainSettings");
	RNA_def_struct_path_func(srna, "rna_SmokeDomainSettings_path");

	prop= RNA_def_property(srna, "maxres", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "maxres");
	RNA_def_property_range(prop, 24, 512);
	RNA_def_property_ui_range(prop, 24, 512, 2, 0);
	RNA_def_property_ui_text(prop, "Max Res", "Maximal resolution used in the fluid domain.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset");

	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "omega");
	RNA_def_property_range(prop, 0.02, 1.0);
	RNA_def_property_ui_range(prop, 0.02, 1.0, 0.02, 2);
	RNA_def_property_ui_text(prop, "Color", "Smoke color (0 = black, 1 = white).");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Smoke_redraw");

	prop= RNA_def_property(srna, "amplify", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "amplify");
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_range(prop, 1, 10, 1, 0);
	RNA_def_property_ui_text(prop, "Amplification", "Enhance the resolution of smoke by this factor using noise.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset");

	prop= RNA_def_property(srna, "highres", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", MOD_SMOKE_HIGHRES);
	RNA_def_property_ui_text(prop, "High res", "Enable high resolution (using amplification).");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset");

	prop= RNA_def_property(srna, "viewhighres", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "viewsettings", MOD_SMOKE_VIEW_USEBIG);
	RNA_def_property_ui_text(prop, "Show high res", "Show high resolution (using amplification).");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, NULL);

	prop= RNA_def_property(srna, "noise_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "noise");
	RNA_def_property_enum_items(prop, prop_noise_type_items);
	RNA_def_property_ui_text(prop, "Noise Method", "Noise method which is used for creating the high resolution");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset");

	prop= RNA_def_property(srna, "visibility", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "visibility");
	RNA_def_property_range(prop, 1, 15);
	RNA_def_property_ui_range(prop, 1, 15, 1, 0);
	RNA_def_property_ui_text(prop, "Display", "How much of the resolution should be shown during preview (every 2nd, 3rd, etc).");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Smoke_redraw");

	prop= RNA_def_property(srna, "alpha", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "alpha");
	RNA_def_property_range(prop, -5.0, 5.0);
	RNA_def_property_ui_range(prop, -5.0, 5.0, 0.02, 5);
	RNA_def_property_ui_text(prop, "Gravity", "Higher value results in sinking smoke");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset");

	prop= RNA_def_property(srna, "beta", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "beta");
	RNA_def_property_range(prop, -5.0, 5.0);
	RNA_def_property_ui_range(prop, -5.0, 5.0, 0.02, 5);
	RNA_def_property_ui_text(prop, "Heat", "Higher value results in faster rising smoke.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset");

	prop= RNA_def_property(srna, "coll_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "coll_group");
	RNA_def_property_struct_type(prop, "Group");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Collision Group", "Limit collisions to this group.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset_dependancy");

	prop= RNA_def_property(srna, "fluid_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "fluid_group");
	RNA_def_property_struct_type(prop, "Group");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Fluid Group", "Limit fluid objects to this group.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset_dependancy");

	prop= RNA_def_property(srna, "eff_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "eff_group");
	RNA_def_property_struct_type(prop, "Group");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Effector Group", "Limit effectors to this group.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset_dependancy");
}

static void rna_def_smoke_flow_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "SmokeFlowSettings", NULL);
	RNA_def_struct_ui_text(srna, "Flow Settings", "Smoke flow settings.");
	RNA_def_struct_sdna(srna, "SmokeFlowSettings");
	RNA_def_struct_path_func(srna, "rna_SmokeFlowSettings_path");

	prop= RNA_def_property(srna, "density", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "density");
	RNA_def_property_range(prop, 0.001, 1);
	RNA_def_property_ui_range(prop, 0.001, 1.0, 1.0, 4);
	RNA_def_property_ui_text(prop, "Density", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, NULL);

	prop= RNA_def_property(srna, "temperature", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "temp");
	RNA_def_property_range(prop, -10, 10);
	RNA_def_property_ui_range(prop, -10, 10, 1, 1);
	RNA_def_property_ui_text(prop, "Temp. Diff.", "Temperature difference to ambientt temperature.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, NULL);
	
	prop= RNA_def_property(srna, "psys", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "psys");
	RNA_def_property_struct_type(prop, "ParticleSystem");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Particle Systems", "Particle systems emitted from the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, "rna_Smoke_reset_dependancy");

	prop= RNA_def_property(srna, "outflow", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "type", MOD_SMOKE_FLOW_TYPE_OUTFLOW);
	RNA_def_property_ui_text(prop, "Outflow", "Deletes smoke from simulation");
	RNA_def_property_update(prop, NC_OBJECT|ND_MODIFIER, NULL);
}

static void rna_def_smoke_coll_settings(BlenderRNA *brna)
{
	StructRNA *srna;

	srna = RNA_def_struct(brna, "SmokeCollSettings", NULL);
	RNA_def_struct_ui_text(srna, "Collision Settings", "Smoke collision settings.");
	RNA_def_struct_sdna(srna, "SmokeCollSettings");
	RNA_def_struct_path_func(srna, "rna_SmokeCollSettings_path");
}

void RNA_def_smoke(BlenderRNA *brna)
{
	rna_def_smoke_domain_settings(brna);
	rna_def_smoke_flow_settings(brna);
	rna_def_smoke_coll_settings(brna);
}

#endif

