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

#include "DNA_curve_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"

#include "WM_types.h"

#include "BKE_utildefines.h"

#ifdef RNA_RUNTIME

static void rna_userdef_lmb_select_set(struct PointerRNA *ptr,int value)
{
	UserDef *userdef = (UserDef*)ptr->data;

	if(value) {
		userdef->flag |= USER_LMOUSESELECT;
		userdef->flag &= ~USER_TWOBUTTONMOUSE;
	}
	else
		userdef->flag &= ~USER_LMOUSESELECT;
}

static void rna_userdef_rmb_select_set(struct PointerRNA *ptr,int value)
{
	rna_userdef_lmb_select_set(ptr, !value);
}

static void rna_userdef_emulate_set(struct PointerRNA *ptr,int value)
{
	UserDef *userdef = (UserDef*)ptr->data;

	if(userdef->flag & USER_LMOUSESELECT) 
		userdef->flag &= ~USER_TWOBUTTONMOUSE;
	else
		userdef->flag ^= USER_TWOBUTTONMOUSE;
}

static int rna_userdef_autokeymode_get(struct PointerRNA *ptr)
{
	UserDef *userdef = (UserDef*)ptr->data;
	short retval = userdef->autokey_mode;
	
	if(!(userdef->autokey_mode & AUTOKEY_ON))
		retval |= AUTOKEY_ON;

	return retval;
}

static void rna_userdef_autokeymode_set(struct PointerRNA *ptr,int value)
{
	UserDef *userdef = (UserDef*)ptr->data;

	if(value == AUTOKEY_MODE_NORMAL) {
		userdef->autokey_mode |= (AUTOKEY_MODE_NORMAL - AUTOKEY_ON);
		userdef->autokey_mode &= ~(AUTOKEY_MODE_EDITKEYS - AUTOKEY_ON);
	}
	else if(value == AUTOKEY_MODE_EDITKEYS) {
		userdef->autokey_mode |= (AUTOKEY_MODE_EDITKEYS - AUTOKEY_ON);
		userdef->autokey_mode &= ~(AUTOKEY_MODE_NORMAL - AUTOKEY_ON);
	}
}

static PointerRNA rna_UserDef_view_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_UserPreferencesView, ptr->data);
}

static PointerRNA rna_UserDef_edit_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_UserPreferencesEdit, ptr->data);
}

static PointerRNA rna_UserDef_autosave_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_UserPreferencesAutosave, ptr->data);
}

static PointerRNA rna_UserDef_language_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_UserPreferencesLanguage, ptr->data);
}

static PointerRNA rna_UserDef_filepaths_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_UserPreferencesFilePaths, ptr->data);
}

static PointerRNA rna_UserDef_system_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_UserPreferencesSystem, ptr->data);
}

#else

static void rna_def_userdef_theme_ui_font_style(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "ThemeFontStyle", NULL);
	RNA_def_struct_sdna(srna, "uiFontStyle");
	RNA_def_struct_ui_text(srna, "Font Style", "Theme settings for Font.");
	
	prop= RNA_def_property(srna, "points", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 6, 48);
	RNA_def_property_ui_text(prop, "Points", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "kerning", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, -5.0, 5.0);
	RNA_def_property_ui_text(prop, "Kerning", "User kerning value in pixels");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "overlap", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "overlap", 1);
	RNA_def_property_ui_text(prop, "Overlap", "Check for overlap characters");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "shadow", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 0, 5);
	RNA_def_property_ui_text(prop, "Shadow Size", "Shadow size in pixels (0, 3 and 5 supported)");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "shadx", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, -10, 10);
	RNA_def_property_ui_text(prop, "Shadow X Offset", "Shadow offset in pixels");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "shady", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, -10, 10);
	RNA_def_property_ui_text(prop, "Shadow Y Offset", "Shadow offset in pixels");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "shadowalpha", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Shadow Alpha", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "shadowcolor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Shadow Brightness", "Shadow color in grey value");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}	

static void rna_def_userdef_theme_ui_style(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	rna_def_userdef_theme_ui_font_style(brna);
	
	srna= RNA_def_struct(brna, "ThemeStyle", NULL);
	RNA_def_struct_sdna(srna, "uiStyle");
	RNA_def_struct_ui_text(srna, "Style", "Theme settings for style sets.");
	
	prop= RNA_def_property(srna, "paneltitle", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "paneltitle");
	RNA_def_property_struct_type(prop, "ThemeFontStyle");
	RNA_def_property_ui_text(prop, "Panel Font", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "grouplabel", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "grouplabel");
	RNA_def_property_struct_type(prop, "ThemeFontStyle");
	RNA_def_property_ui_text(prop, "Group Label Font", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "widgetlabel", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "widgetlabel");
	RNA_def_property_struct_type(prop, "ThemeFontStyle");
	RNA_def_property_ui_text(prop, "Widget Label Font", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "widget", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "widget");
	RNA_def_property_struct_type(prop, "ThemeFontStyle");
	RNA_def_property_ui_text(prop, "Widget Font", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
}	

static void rna_def_userdef_theme_ui_wcol(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "ThemeWidgetColors", NULL);
	RNA_def_struct_sdna(srna, "uiWidgetColors");
	RNA_def_struct_ui_text(srna, "Theme Widget Color Set", "Theme settings for widget color sets.");
		
	prop= RNA_def_property(srna, "outline", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Outline", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "inner", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Inner", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "inner_sel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Inner Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "item", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Item", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "text", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Text", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "text_sel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Text Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "shaded", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shaded", 1);
	RNA_def_property_ui_text(prop, "Shaded", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "shadetop", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, -100, 100);
	RNA_def_property_ui_text(prop, "Shade Top", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "shadedown", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, -100, 100);
	RNA_def_property_ui_text(prop, "Shade Down", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
}

static void rna_def_userdef_theme_ui(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	rna_def_userdef_theme_ui_wcol(brna);
	
	srna= RNA_def_struct(brna, "ThemeUserInterface", NULL);
	RNA_def_struct_sdna(srna, "ThemeUI");
	RNA_def_struct_ui_text(srna, "Theme User Interface", "Theme settings for user interface elements.");

	prop= RNA_def_property(srna, "wcol_regular", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_regular");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Regular Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_tool", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_tool");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Tool Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_radio", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_radio");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Radio Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_text", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_text");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Text Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_option", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_option");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Option Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "wcol_toggle", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_toggle");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Toggle Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_num", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_num");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Number Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_numslider", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_numslider");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Slider Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_box", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_box");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Box Backdrop Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_menu", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_menu");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Menu Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_pulldown", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_pulldown");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Pulldown Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_menu_back", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_menu_back");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Menu Backdrop Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "wcol_menu_item", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_menu_item");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Menu Item Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "wcol_scroll", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "wcol_scroll");
	RNA_def_property_struct_type(prop, "ThemeWidgetColors");
	RNA_def_property_ui_text(prop, "Scroll Widget Colors", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "icon_file", PROP_STRING, PROP_FILEPATH);
	RNA_def_property_string_sdna(prop, NULL, "iconfile");
	RNA_def_property_ui_text(prop, "Icon File", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_spaces_main(StructRNA *srna, int spacetype)
{
	PropertyRNA *prop;

	/* window */
	prop= RNA_def_property(srna, "back", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Back", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "title", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Title", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "text", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Text", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "text_hi", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Text Highlight", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	/* header */
	prop= RNA_def_property(srna, "header", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Header", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "header_text", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Header Text", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "header_text_hi", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Header Text Highlight", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	/* buttons */
	if(! ELEM(spacetype, SPACE_BUTS, SPACE_OUTLINER)) {
		prop= RNA_def_property(srna, "button", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "Button Back", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
		
		prop= RNA_def_property(srna, "button_title", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "Button Title", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
		
		prop= RNA_def_property(srna, "button_text", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "Button Text", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
		
		prop= RNA_def_property(srna, "button_text_hi", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "Button Text Highlight", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
	}
	
	/* list/channels */
	if(ELEM4(spacetype, SPACE_IPO, SPACE_ACTION, SPACE_NLA, SPACE_NODE)) {
		prop= RNA_def_property(srna, "list", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "List Back", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
		
		prop= RNA_def_property(srna, "list_title", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "List Title", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
		
		prop= RNA_def_property(srna, "list_text", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "List Text", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
		
		prop= RNA_def_property(srna, "list_text_hi", PROP_FLOAT, PROP_COLOR);
		RNA_def_property_array(prop, 3);
		RNA_def_property_ui_text(prop, "List Text Highlight", "");
		RNA_def_property_update(prop, NC_WINDOW, NULL);
	}	
}

static void rna_def_userdef_theme_spaces_vertex(StructRNA *srna)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "vertex", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Vertex", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "vertex_select", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Vertex Select", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "vertex_size", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_text(prop, "Vertex Size", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_spaces_edge(StructRNA *srna)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "edge_select", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "edge Select", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "edge_seam", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Edge Seam", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "edge_sharp", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Edge Sharp", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "edge_facesel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Edge UV Face Select", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_spaces_face(StructRNA *srna)
{
	PropertyRNA *prop;

	prop= RNA_def_property(srna, "face", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Face", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "face_select", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Face Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "face_dot", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Face Dot Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "facedot_size", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_text(prop, "Face Dot Size", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_view3d(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_view3d */

	srna= RNA_def_struct(brna, "ThemeView3D", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme 3D View", "Theme settings for the 3D View.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_VIEW3D);

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "panel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Panel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "wire", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Wire", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "lamp", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Lamp", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "object_selected", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "select");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Object Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "object_active", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "active");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Active Object", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "object_grouped", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "group");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Object Grouped", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "object_grouped_active", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "group_active");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Object Grouped Active", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "transform", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Transform", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	rna_def_userdef_theme_spaces_vertex(srna);
	rna_def_userdef_theme_spaces_edge(srna);
	rna_def_userdef_theme_spaces_face(srna);

	prop= RNA_def_property(srna, "editmesh_active", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Active Vert/Edge/Face", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "normal", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Normal", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "bone_solid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Bone Solid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "bone_pose", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Bone Pose", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_graph(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_graph */

	srna= RNA_def_struct(brna, "ThemeGraphEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Graph Editor", "Theme settings for the Ipo Editor.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_IPO);

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "panel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Panel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "window_sliders", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Sliders", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "channels_region", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade2");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Channels Region", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	rna_def_userdef_theme_spaces_vertex(srna);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "handle_vertex", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Handle Vertex", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "handle_vertex_select", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Handle Vertex Select", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "handle_vertex_size", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 0, 255);
	RNA_def_property_ui_text(prop, "Handle Vertex Size", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "channel_group", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "group");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Channel Group", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "active_channels_group", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "group_active");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Active Channel Group", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "dopesheet_channel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "ds_channel");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "DopeSheet Channel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "dopesheet_subchannel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "ds_subchannel");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "DopeSheet Sub-Channel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_file(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_file  */

	srna= RNA_def_struct(brna, "ThemeFileBrowser", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme File Browser", "Theme settings for the File Browser.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_FILE);

	prop= RNA_def_property(srna, "selected_file", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "hilite");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Selected File", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "tiles", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "panel");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Tiles", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "scrollbar", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Scrollbar", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "scroll_handle", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade2");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Scroll Handle", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "active_file", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "active");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Active File", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "active_file_text", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "grid");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Active File Text", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_outliner(BlenderRNA *brna)
{
	StructRNA *srna;

	/* space_outliner */

	srna= RNA_def_struct(brna, "ThemeOutliner", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Outliner", "Theme settings for the Outliner.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_OUTLINER);
}

static void rna_def_userdef_theme_space_info(BlenderRNA *brna)
{
	StructRNA *srna;

	/* space_info */

	srna= RNA_def_struct(brna, "ThemeUserPreferences", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme User Preferences", "Theme settings for the User Preferences.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_INFO);
}

static void rna_def_userdef_theme_space_text(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_text */

	srna= RNA_def_struct(brna, "ThemeTextEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Text Editor", "Theme settings for the Text Editor.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_TEXT);

	prop= RNA_def_property(srna, "line_numbers_background", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "grid");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Line Numbers Background", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "scroll_bar", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Scroll Bar", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "selected_text", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade2");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Selected Text", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "cursor", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "hilite");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Cursor", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "syntax_builtin", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxb");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Syntax Builtin", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "syntax_special", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxv");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Syntax Special", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "syntax_comment", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxc");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Syntax Comment", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "syntax_string", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxl");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Syntax String", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "syntax_numbers", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxn");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Syntax Numbers", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_node(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_node */

	srna= RNA_def_struct(brna, "ThemeNodeEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Node Editor", "Theme settings for the Node Editor.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_NODE);

	prop= RNA_def_property(srna, "wires", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "wire");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Wires", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "wire_select", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "edge_select");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Wire Select", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "selected_text", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade2");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Selected Text", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "node_backdrop", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxl");
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Node Backdrop", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "in_out_node", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxn");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "In/Out Node", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "converter_node", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxv");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Converter Node", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "operator_node", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxb");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Operator Node", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "group_node", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "syntaxc");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Group Node", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_logic(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	/* space_buts */
	
	srna= RNA_def_struct(brna, "ThemeLogicEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Logic Editor", "Theme settings for the Logic Editor.");
	
	rna_def_userdef_theme_spaces_main(srna, SPACE_LOGIC);
	
	prop= RNA_def_property(srna, "panel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Panel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}


static void rna_def_userdef_theme_space_buts(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_buts */

	srna= RNA_def_struct(brna, "ThemeButtonsWindow", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Buttons Window", "Theme settings for the Buttons Window.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_BUTS);

	prop= RNA_def_property(srna, "panel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Panel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_time(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_time */

	srna= RNA_def_struct(brna, "ThemeTimeline", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Timeline", "Theme settings for the Timeline.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_TIME);

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_sound(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_sound */

	srna= RNA_def_struct(brna, "ThemeAudioWindow", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Audio Window", "Theme settings for the Audio Window.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_SOUND);

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "window_sliders", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Sliders", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_image(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_image */

	srna= RNA_def_struct(brna, "ThemeImageEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Image Editor", "Theme settings for the Image Editor.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_IMAGE);
	rna_def_userdef_theme_spaces_vertex(srna);
	rna_def_userdef_theme_spaces_face(srna);

	prop= RNA_def_property(srna, "editmesh_active", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "Active Vert/Edge/Face", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_seq(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_seq */

	srna= RNA_def_struct(brna, "ThemeSequenceEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme Sequence Editor", "Theme settings for the Sequence Editor.");

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "window_sliders", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Window Sliders", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "movie_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "movie");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Movie Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "image_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "image");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Image Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "scene_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "scene");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Scene Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "audio_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "audio");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Audio Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "effect_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "effect");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Effect Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "plugin_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "plugin");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Plugin Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "transition_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "transition");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Transition Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "meta_strip", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "meta");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Meta Strip", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "keyframe", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "vertex_select");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Keyframe", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "draw_action", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "bone_pose");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Draw Action", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_action(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_action */

	srna= RNA_def_struct(brna, "ThemeDopeSheet", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme DopeSheet", "Theme settings for the DopeSheet.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_ACTION);

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "value_sliders", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "face");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Value Sliders", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "view_sliders", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "View Sliders", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "channels", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade2");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Channels", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "channels_selected", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "hilite");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Channels Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "channel_group", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "group");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Channel Group", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "active_channels_group", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "group_active");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Active Channel Group", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "long_key", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "strip");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Long Key", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "long_key_selected", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "strip_select");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Long Key Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "dopesheet_channel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "ds_channel");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "DopeSheet Channel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "dopesheet_subchannel", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "ds_subchannel");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "DopeSheet Sub-Channel", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_space_nla(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* space_nla */

	srna= RNA_def_struct(brna, "ThemeNLAEditor", NULL);
	RNA_def_struct_sdna(srna, "ThemeSpace");
	RNA_def_struct_ui_text(srna, "Theme NLA Editor", "Theme settings for the NLA Editor.");

	rna_def_userdef_theme_spaces_main(srna, SPACE_NLA);

	prop= RNA_def_property(srna, "grid", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Grid", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "view_sliders", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "View Sliders", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	prop= RNA_def_property(srna, "bars", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "shade2");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Bars", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "bars_selected", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "hilite");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Bars Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "strips", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "strip");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "strips", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "strips_selected", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "strip_select");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Strips Selected", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "current_frame", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "cframe");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_theme_colorset(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ThemeBoneColorSet", NULL);
	RNA_def_struct_sdna(srna, "ThemeWireColor");
	RNA_def_struct_ui_text(srna, "Theme Bone Color Set", "Theme settings for bone color sets.");

	prop= RNA_def_property(srna, "normal", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "solid");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Normal", "Color used for the surface of bones.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "selected", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "select");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Selected", "Color used for selected bones.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "active", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Active", "Color used for active bones.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "colored_constraints", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TH_WIRECOLOR_CONSTCOLS);
	RNA_def_property_ui_text(prop, "Colored Constraints", "Allow the use of colors indicating constraints/keyed status.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_themes(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Theme", NULL);
	RNA_def_struct_sdna(srna, "bTheme");
	RNA_def_struct_ui_text(srna, "Theme", "Theme settings defining draw style and colors in the user interface.");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Name of the theme.");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "user_interface", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tui");
	RNA_def_property_struct_type(prop, "ThemeUserInterface");
	RNA_def_property_ui_text(prop, "User Interface", "");

	prop= RNA_def_property(srna, "view_3d", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tv3d");
	RNA_def_property_struct_type(prop, "ThemeView3D");
	RNA_def_property_ui_text(prop, "3D View", "");

	prop= RNA_def_property(srna, "graph_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tipo");
	RNA_def_property_struct_type(prop, "ThemeGraphEditor");
	RNA_def_property_ui_text(prop, "Graph Editor", "");

	prop= RNA_def_property(srna, "file_browser", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tfile");
	RNA_def_property_struct_type(prop, "ThemeFileBrowser");
	RNA_def_property_ui_text(prop, "File Browser", "");

	prop= RNA_def_property(srna, "nla_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tnla");
	RNA_def_property_struct_type(prop, "ThemeNLAEditor");
	RNA_def_property_ui_text(prop, "NLA Editor", "");

	prop= RNA_def_property(srna, "dopesheet_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tact");
	RNA_def_property_struct_type(prop, "ThemeDopeSheet");
	RNA_def_property_ui_text(prop, "DopeSheet", "");

	prop= RNA_def_property(srna, "image_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tima");
	RNA_def_property_struct_type(prop, "ThemeImageEditor");
	RNA_def_property_ui_text(prop, "Image Editor", "");

	prop= RNA_def_property(srna, "sequence_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tseq");
	RNA_def_property_struct_type(prop, "ThemeSequenceEditor");
	RNA_def_property_ui_text(prop, "Sequence Editor", "");

	prop= RNA_def_property(srna, "buttons_window", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tbuts");
	RNA_def_property_struct_type(prop, "ThemeButtonsWindow");
	RNA_def_property_ui_text(prop, "Buttons Window", "");

	prop= RNA_def_property(srna, "text_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "text");
	RNA_def_property_struct_type(prop, "ThemeTextEditor");
	RNA_def_property_ui_text(prop, "Text Editor", "");

	prop= RNA_def_property(srna, "timeline", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "ttime");
	RNA_def_property_struct_type(prop, "ThemeTimeline");
	RNA_def_property_ui_text(prop, "Timeline", "");

	prop= RNA_def_property(srna, "node_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tnode");
	RNA_def_property_struct_type(prop, "ThemeNodeEditor");
	RNA_def_property_ui_text(prop, "Node Editor", "");

	prop= RNA_def_property(srna, "logic_editor", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tlogic");
	RNA_def_property_struct_type(prop, "ThemeLogicEditor");
	RNA_def_property_ui_text(prop, "Logic Editor", "");
	
	prop= RNA_def_property(srna, "outliner", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "toops");
	RNA_def_property_struct_type(prop, "ThemeOutliner");
	RNA_def_property_ui_text(prop, "Outliner", "");

	prop= RNA_def_property(srna, "user_preferences", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "tinfo");
	RNA_def_property_struct_type(prop, "ThemeUserPreferences");
	RNA_def_property_ui_text(prop, "User Preferences", "");

	prop= RNA_def_property(srna, "bone_color_sets", PROP_COLLECTION, PROP_NEVER_NULL);
	RNA_def_property_collection_sdna(prop, NULL, "tarm", "");
	RNA_def_property_struct_type(prop, "ThemeBoneColorSet");
	RNA_def_property_ui_text(prop, "Bone Color Sets", "");
}

static void rna_def_userdef_dothemes(BlenderRNA *brna)
{
	
	rna_def_userdef_theme_ui_style(brna);
	rna_def_userdef_theme_ui(brna);
	
	rna_def_userdef_theme_space_view3d(brna);
	rna_def_userdef_theme_space_graph(brna);
	rna_def_userdef_theme_space_file(brna);
	rna_def_userdef_theme_space_nla(brna);
	rna_def_userdef_theme_space_action(brna);
	rna_def_userdef_theme_space_image(brna);
	rna_def_userdef_theme_space_seq(brna);
	rna_def_userdef_theme_space_buts(brna);
	rna_def_userdef_theme_space_text(brna);
	rna_def_userdef_theme_space_time(brna);
	rna_def_userdef_theme_space_node(brna);
	rna_def_userdef_theme_space_outliner(brna);
	rna_def_userdef_theme_space_info(brna);
	rna_def_userdef_theme_space_sound(brna);
	rna_def_userdef_theme_space_logic(brna);
	rna_def_userdef_theme_colorset(brna);
	rna_def_userdef_themes(brna);
}

static void rna_def_userdef_solidlight(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "UserSolidLight", NULL);
	RNA_def_struct_sdna(srna, "SolidLight");
	RNA_def_struct_ui_text(srna, "Solid Light", "Light used for OpenGL lighting in solid draw mode.");
	
	prop= RNA_def_property(srna, "enabled", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", 1);
	RNA_def_property_ui_text(prop, "Enabled", "Enable this OpenGL light in solid draw mode.");

	prop= RNA_def_property(srna, "direction", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "vec");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Direction", "The direction that the OpenGL light is shining.");

	prop= RNA_def_property(srna, "diffuse_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "col");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Diffuse Color", "The diffuse color of the OpenGL light.");

	prop= RNA_def_property(srna, "specular_color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "spec");
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Specular Color", "The color of the lights specular highlight.");
}

static void rna_def_userdef_view(BlenderRNA *brna)
{
	PropertyRNA *prop;
	StructRNA *srna;

	static EnumPropertyItem view_zoom_styles[] = {
		{USER_ZOOM_CONT, "CONTINUE", 0, "Continue", "Old style zoom, continues while moving mouse up or down."},
		{USER_ZOOM_DOLLY, "DOLLY", 0, "Dolly", "Zooms in and out based on vertical mouse movement."},
		{USER_ZOOM_SCALE, "SCALE", 0, "Scale", "Zooms in and out like scaling the view, mouse movements relative to center."},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem view_rotation_items[] = {
		{0, "TURNTABLE", 0, "Turntable", "Use turntable style rotation in the viewport."},
		{USER_TRACKBALL, "TRACKBALL", 0, "Trackball", "Use trackball style rotation in the viewport."},
		{0, NULL, 0, NULL, NULL}};


	srna= RNA_def_struct(brna, "UserPreferencesView", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_nested(brna, srna, "UserPreferences");
	RNA_def_struct_ui_text(srna, "View & Controls", "Preferences related to viewing data");

	/* View and Controls  */

	/* display */
	prop= RNA_def_property(srna, "tooltips", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_TOOLTIPS);
	RNA_def_property_ui_text(prop, "Tooltips", "Display tooltips.");

	prop= RNA_def_property(srna, "display_object_info", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_DRAWVIEWINFO);
	RNA_def_property_ui_text(prop, "Display Object Info", "Display objects name and frame number in 3d view.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "global_scene", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_SCENEGLOBAL);
	RNA_def_property_ui_text(prop, "Global Scene", "Forces the current Scene to be displayed in all Screens.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "use_large_cursors", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "curssize", 0);
	RNA_def_property_ui_text(prop, "Large Cursors", "Use large mouse cursors when available.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "show_view_name", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_SHOW_VIEWPORTNAME);
	RNA_def_property_ui_text(prop, "Show View Name", "Show the name of the view's direction in each 3D View.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "show_playback_fps", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_SHOW_FPS);
	RNA_def_property_ui_text(prop, "Show Playback FPS", "Show the frames per second screen refresh rate, while animation is played back.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
	
	/* menus */
	prop= RNA_def_property(srna, "open_mouse_over", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_MENUOPENAUTO);
	RNA_def_property_ui_text(prop, "Open On Mouse Over", "Open menu buttons and pulldowns automatically when the mouse is hovering.");
	
	prop= RNA_def_property(srna, "open_toplevel_delay", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "menuthreshold1");
	RNA_def_property_range(prop, 1, 40);
	RNA_def_property_ui_text(prop, "Top Level Menu Open Delay", "Time delay in 1/10 seconds before automatically opening top level menus.");

	prop= RNA_def_property(srna, "open_sublevel_delay", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "menuthreshold2");
	RNA_def_property_range(prop, 1, 40);
	RNA_def_property_ui_text(prop, "Sub Level Menu Open Delay", "Time delay in 1/10 seconds before automatically opening sub level menus.");

	/* Toolbox click-hold delay */
	prop= RNA_def_property(srna, "open_left_mouse_delay", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tb_leftmouse");
	RNA_def_property_range(prop, 1, 40);
	RNA_def_property_ui_text(prop, "Hold LMB Open Toolbox Delay", "Time in 1/10 seconds to hold the Left Mouse Button before opening the toolbox.");

	prop= RNA_def_property(srna, "open_right_mouse_delay", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tb_rightmouse");
	RNA_def_property_range(prop, 1, 40);
	RNA_def_property_ui_text(prop, "Hold RMB Open Toolbox Delay", "Time in 1/10 seconds to hold the Right Mouse Button before opening the toolbox.");

	prop= RNA_def_property(srna, "pin_floating_panels", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_PANELPINNED);
	RNA_def_property_ui_text(prop, "Pin Floating Panels", "Make floating panels invoked by a hotkey (eg. N Key) open at the previous location.");

	prop= RNA_def_property(srna, "use_column_layout", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_PLAINMENUS);
	RNA_def_property_ui_text(prop, "Toolbox Column Layout", "Use a column layout for toolbox.");

	prop= RNA_def_property(srna, "directional_menus", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "uiflag", USER_MENUFIXEDORDER);
	RNA_def_property_ui_text(prop, "Contents Follow Opening Direction", "Otherwise menus, etc will always be top to bottom, left to right, no matter opening direction.");

	/* snap to grid */
	prop= RNA_def_property(srna, "snap_translate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_AUTOGRABGRID);
	RNA_def_property_ui_text(prop, "Enable Translation Snap", "Snap objects and sub-objects to grid units when moving.");

	prop= RNA_def_property(srna, "snap_rotate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_AUTOROTGRID);
	RNA_def_property_ui_text(prop, "Enable Rotation Snap", "Snap objects and sub-objects to grid units when rotating.");

	prop= RNA_def_property(srna, "snap_scale", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_AUTOSIZEGRID);
	RNA_def_property_ui_text(prop, "Enable Scaling Snap", "Snap objects and sub-objects to grid units when scaling.");

	prop= RNA_def_property(srna, "auto_depth", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_ORBIT_ZBUF);
	RNA_def_property_ui_text(prop, "Auto Depth", "Use the depth under the mouse to improve view pan/rotate/zoom functionality.");

	prop= RNA_def_property(srna, "global_pivot", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_LOCKAROUND);
	RNA_def_property_ui_text(prop, "Global Pivot", "Lock the same rotation/scaling pivot in all 3D Views.");

	/* view zoom */
	prop= RNA_def_property(srna, "viewport_zoom_style", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "viewzoom");
	RNA_def_property_enum_items(prop, view_zoom_styles);
	RNA_def_property_ui_text(prop, "Viewport Zoom Style", "Which style to use for viewport scaling.");

	prop= RNA_def_property(srna, "zoom_to_mouse", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_ZOOM_TO_MOUSEPOS);
	RNA_def_property_ui_text(prop, "Zoom To Mouse Position", "Zoom in towards the mouse pointer's position in the 3D view, rather than the 2D window center.");

	/* view rotation */
	prop= RNA_def_property(srna, "view_rotation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "flag");
	RNA_def_property_enum_items(prop, view_rotation_items);
	RNA_def_property_ui_text(prop, "View Rotation", "Rotation style in the viewport.");

	prop= RNA_def_property(srna, "perspective_orthographic_switch", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_AUTOPERSP);
	RNA_def_property_ui_text(prop, "Perspective/Orthographic Switch", "Automatically switch between orthographic and perspective when changing from top/front/side views.");

	prop= RNA_def_property(srna, "rotate_around_selection", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_ORBIT_SELECTION);
	RNA_def_property_ui_text(prop, "Rotate Around Selection", "Use selection as the orbiting center.");

	/* select with */
	prop= RNA_def_property(srna, "left_mouse_button_select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_LMOUSESELECT);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_userdef_lmb_select_set");
	RNA_def_property_ui_text(prop, "Left Mouse Button Select", "Use left Mouse Button for selection.");
	
	prop= RNA_def_property(srna, "right_mouse_button_select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", USER_LMOUSESELECT);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_userdef_rmb_select_set");
	RNA_def_property_ui_text(prop, "Right Mouse Button Select", "Use Right Mouse Button for selection.");
	
	prop= RNA_def_property(srna, "emulate_3_button_mouse", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_TWOBUTTONMOUSE);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_userdef_emulate_set");
	RNA_def_property_ui_text(prop, "Emulate 3 Button Mouse", "Emulates Middle Mouse with Alt+LeftMouse (doesnt work with Left Mouse Select option.)");
	
	prop= RNA_def_property(srna, "use_middle_mouse_paste", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_MMB_PASTE);
	RNA_def_property_ui_text(prop, "Middle Mouse Paste", "In text window, paste with middle mouse button instead of panning.");

	prop= RNA_def_property(srna, "show_mini_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_SHOW_ROTVIEWICON);
	RNA_def_property_ui_text(prop, "Show Mini Axis", "Show a small rotating 3D axis in the bottom left corner of the 3D View.");

	prop= RNA_def_property(srna, "mini_axis_size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "rvisize");
	RNA_def_property_range(prop, 10, 64);
	RNA_def_property_ui_text(prop, "Mini Axis Size", "The axis icon's size.");

	prop= RNA_def_property(srna, "mini_axis_brightness", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "rvibright");
	RNA_def_property_range(prop, 0, 10);
	RNA_def_property_ui_text(prop, "Mini Axis Brightness", "The brightness of the icon.");

	/* middle mouse button */
	prop= RNA_def_property(srna, "middle_mouse_rotate", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", USER_VIEWMOVE);
	RNA_def_property_ui_text(prop, "Middle Mouse Rotate", "Use the middle mouse button for rotation the viewport.");

	prop= RNA_def_property(srna, "middle_mouse_pan", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_VIEWMOVE);
	RNA_def_property_ui_text(prop, "Middle Mouse Pan", "Use the middle mouse button for panning the viewport.");

	prop= RNA_def_property(srna, "wheel_invert_zoom", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_WHEELZOOMDIR);
	RNA_def_property_ui_text(prop, "Wheel Invert Zoom", "Swap the Mouse Wheel zoom direction.");

	prop= RNA_def_property(srna, "wheel_scroll_lines", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "wheellinescroll");
	RNA_def_property_range(prop, 0, 32);
	RNA_def_property_ui_text(prop, "Wheel Scroll Lines", "The number of lines scrolled at a time with the mouse wheel.");

	prop= RNA_def_property(srna, "smooth_view", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "smooth_viewtx");
	RNA_def_property_range(prop, 0, 1000);
	RNA_def_property_ui_text(prop, "Smooth View", "The time to animate the view in milliseconds, zero to disable.");

	prop= RNA_def_property(srna, "rotation_angle", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "pad_rot_angle");
	RNA_def_property_range(prop, 0, 90);
	RNA_def_property_ui_text(prop, "Rotation Angle", "The rotation step for numerical pad keys (2 4 6 8).");

	/* 3D transform widget */
	prop= RNA_def_property(srna, "use_manipulator", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "tw_flag", 1);
	RNA_def_property_ui_text(prop, "Manipulator", "Use 3d transform manipulator.");

	prop= RNA_def_property(srna, "manipulator_size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tw_size");
	RNA_def_property_range(prop, 2, 40);
	RNA_def_property_ui_text(prop, "Manipulator Size", "Diameter of widget, in 10 pixel units.");

	prop= RNA_def_property(srna, "manipulator_handle_size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tw_handlesize");
	RNA_def_property_range(prop, 2, 40);
	RNA_def_property_ui_text(prop, "Manipulator Handle Size", "Size of widget handles as percentage of widget radius.");

	prop= RNA_def_property(srna, "manipulator_hotspot", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tw_hotspot");
	RNA_def_property_range(prop, 4, 40);
	RNA_def_property_ui_text(prop, "Manipulator Hotspot", "Hotspot in pixels for clicking widget handles.");

	prop= RNA_def_property(srna, "object_center_size", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "obcenter_dia");
	RNA_def_property_range(prop, 4, 10);
	RNA_def_property_ui_text(prop, "Object Center Size", "Diameter in Pixels for Object/Lamp center display.");

	prop= RNA_def_property(srna, "ndof_pan_speed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ndof_pan");
	RNA_def_property_range(prop, 0, 200);
	RNA_def_property_ui_text(prop, "NDof Pan Speed", "The overall panning speed of an NDOF device, as percent of standard.");

	prop= RNA_def_property(srna, "ndof_rotate_speed", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "ndof_rotate");
	RNA_def_property_range(prop, 0, 200);
	RNA_def_property_ui_text(prop, "NDof Rotation Speed", "The overall rotation speed of an NDOF device, as percent of standard.");
}

static void rna_def_userdef_edit(BlenderRNA *brna)
{
	PropertyRNA *prop;
	StructRNA *srna;

	static EnumPropertyItem auto_key_modes[] = {
		{AUTOKEY_MODE_NORMAL, "ADD_REPLACE_KEYS", 0, "Add/Replace Keys", ""},
		{AUTOKEY_MODE_EDITKEYS, "REPLACE_KEYS", 0, "Replace Keys", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem new_interpolation_types[] = {
		{BEZT_IPO_CONST, "CONSTANT", 0, "Constant", ""},
		{BEZT_IPO_LIN, "LINEAR", 0, "Linear", ""},
		{BEZT_IPO_BEZ, "BEZIER", 0, "Bezier", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "UserPreferencesEdit", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_nested(brna, srna, "UserPreferences");
	RNA_def_struct_ui_text(srna, "Edit Methods", "Settings for interacting with Blender data.");
	
	/* Edit Methods */
	prop= RNA_def_property(srna, "material_linked_object", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_MAT_ON_OB);
	RNA_def_property_ui_text(prop, "Material Linked Object", "Toggle whether the material is linked to object data or the object block.");

	prop= RNA_def_property(srna, "material_linked_obdata", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", USER_MAT_ON_OB);
	RNA_def_property_ui_text(prop, "Material Linked ObData", "Toggle whether the material is linked to object data or the object block.");

	prop= RNA_def_property(srna, "enter_edit_mode", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_ADD_EDITMODE);
	RNA_def_property_ui_text(prop, "Enter Edit Mode", "Enter Edit Mode automatically after adding a new object.");

	prop= RNA_def_property(srna, "align_to_view", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_ADD_VIEWALIGNED);
	RNA_def_property_ui_text(prop, "Align To View", "Align newly added objects facing the 3D View direction.");

	prop= RNA_def_property(srna, "drag_immediately", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_DRAGIMMEDIATE);
	RNA_def_property_ui_text(prop, "Drag Immediately", "Moving things with a mouse drag doesn't require a click to confirm (Best for tablet users).");

	prop= RNA_def_property(srna, "undo_steps", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "undosteps");
	RNA_def_property_range(prop, 0, 64);
	RNA_def_property_ui_text(prop, "Undo Steps", "Number of undo steps available (smaller values conserve memory).");

	prop= RNA_def_property(srna, "undo_memory_limit", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "undomemory");
	RNA_def_property_range(prop, 0, 32767);
	RNA_def_property_ui_text(prop, "Undo Memory Size", "Maximum memory usage in megabytes (0 means unlimited).");

	prop= RNA_def_property(srna, "global_undo", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_GLOBALUNDO);
	RNA_def_property_ui_text(prop, "Global Undo", "Global undo works by keeping a full copy of the file itself in memory, so takes extra memory.");

	prop= RNA_def_property(srna, "auto_keying_enable", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "autokey_mode", AUTOKEY_ON);
	RNA_def_property_ui_text(prop, "Auto Keying Enable", "Automatic keyframe insertion for Objects and Bones.");

	prop= RNA_def_property(srna, "auto_keying_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, auto_key_modes);
	RNA_def_property_enum_funcs(prop, "rna_userdef_autokeymode_get", "rna_userdef_autokeymode_set", NULL);
	RNA_def_property_ui_text(prop, "Auto Keying Mode", "Mode of automatic keyframe insertion for Objects and Bones.");

	prop= RNA_def_property(srna, "auto_keyframe_insert_available", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "autokey_flag", AUTOKEY_FLAG_INSERTAVAIL);
	RNA_def_property_ui_text(prop, "Auto Keyframe Insert Available", "Automatic keyframe insertion in available curves.");

	prop= RNA_def_property(srna, "auto_keyframe_insert_needed", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "autokey_flag", AUTOKEY_FLAG_INSERTNEEDED);
	RNA_def_property_ui_text(prop, "Auto Keyframe Insert Needed", "Automatic keyframe insertion only when keyframe needed.");

	prop= RNA_def_property(srna, "use_visual_keying", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "autokey_flag", AUTOKEY_FLAG_AUTOMATKEY);
	RNA_def_property_ui_text(prop, "Visual Keying", "Use Visual keying automatically for constrained objects.");

	prop= RNA_def_property(srna, "new_interpolation_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, new_interpolation_types);
	RNA_def_property_enum_sdna(prop, NULL, "ipo_new");
	RNA_def_property_ui_text(prop, "New Interpolation Type", "");

	prop= RNA_def_property(srna, "grease_pencil_manhattan_distance", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gp_manhattendist");
	RNA_def_property_range(prop, 0, 100);
	RNA_def_property_ui_text(prop, "Grease Pencil Manhattan Distance", "Pixels moved by mouse per axis when drawing stroke.");

	prop= RNA_def_property(srna, "grease_pencil_euclidean_distance", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gp_euclideandist");
	RNA_def_property_range(prop, 0, 100);
	RNA_def_property_ui_text(prop, "Grease Pencil Euclidean Distance", "Distance moved by mouse when drawing stroke (in pixels) to include.");

	prop= RNA_def_property(srna, "grease_pencil_smooth_stroke", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gp_settings", GP_PAINT_DOSMOOTH);
	RNA_def_property_ui_text(prop, "Grease Pencil Smooth Stroke", "Smooth the final stroke.");

#if 0
	prop= RNA_def_property(srna, "grease_pencil_simplify_stroke", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gp_settings", GP_PAINT_DOSIMPLIFY);
	RNA_def_property_ui_text(prop, "Grease Pencil Simplify Stroke", "Simplify the final stroke.");
#endif

	prop= RNA_def_property(srna, "grease_pencil_eraser_radius", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gp_eraser");
	RNA_def_property_range(prop, 0, 100);
	RNA_def_property_ui_text(prop, "Grease Pencil Eraser Radius", "Radius of eraser 'brush'.");

	prop= RNA_def_property(srna, "duplicate_mesh", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_MESH);
	RNA_def_property_ui_text(prop, "Duplicate Mesh", "Causes mesh data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_surface", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_SURF);
	RNA_def_property_ui_text(prop, "Duplicate Surface", "Causes surface data to be duplicated with Shift+D.");
	
	prop= RNA_def_property(srna, "duplicate_curve", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_CURVE);
	RNA_def_property_ui_text(prop, "Duplicate Curve", "Causes curve data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_text", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_FONT);
	RNA_def_property_ui_text(prop, "Duplicate Text", "Causes text data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_metaball", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_MBALL);
	RNA_def_property_ui_text(prop, "Duplicate Metaball", "Causes metaball data to be duplicated with Shift+D.");
	
	prop= RNA_def_property(srna, "duplicate_armature", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_ARM);
	RNA_def_property_ui_text(prop, "Duplicate Armature", "Causes armature data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_lamp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_LAMP);
	RNA_def_property_ui_text(prop, "Duplicate Lamp", "Causes lamp data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_material", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_MAT);
	RNA_def_property_ui_text(prop, "Duplicate Material", "Causes material data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_texture", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_TEX);
	RNA_def_property_ui_text(prop, "Duplicate Texture", "Causes texture data to be duplicated with Shift+D.");
	
	prop= RNA_def_property(srna, "duplicate_ipo", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_IPO);
	RNA_def_property_ui_text(prop, "Duplicate Ipo", "Causes ipo data to be duplicated with Shift+D.");

	prop= RNA_def_property(srna, "duplicate_action", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dupflag", USER_DUP_ACT);
	RNA_def_property_ui_text(prop, "Duplicate Action", "Causes actions to be duplicated with Shift+D.");
}

static void rna_def_userdef_language(BlenderRNA *brna)
{
	PropertyRNA *prop;
	StructRNA *srna;
	
	/* hardcoded here, could become dynamic somehow */
	static EnumPropertyItem language_items[] = {
		{0, "ENGLISH", 0, "English", ""},
		{1, "JAPANESE", 0, "Japanese", ""},
		{2, "DUTCH", 0, "Dutch", ""},
		{3, "ITALIAN", 0, "Italian", ""},
		{4, "GERMAN", 0, "German", ""},
		{5, "FINNISH", 0, "Finnish", ""},
		{6, "SWEDISH", 0, "Swedish", ""},
		{7, "FRENCH", 0, "French", ""},
		{8, "SPANISH", 0, "Spanish", ""},
		{9, "CATALAN", 0, "Catalan", ""},
		{10, "CZECH", 0, "Czech", ""},
		{11, "BRAZILIAN_PORTUGUESE", 0, "Brazilian Portuguese", ""},
		{12, "SIMPLIFIED_CHINESE", 0, "Simplified Chinese", ""},
		{13, "RUSSIAN", 0, "Russian", ""},
		{14, "CROATIAN", 0, "Croatian", ""},
		{15, "SERBIAN", 0, "Serbian", ""},
		{16, "UKRAINIAN", 0, "Ukrainian", ""},
		{17, "POLISH", 0, "Polish", ""},
		{18, "ROMANIAN", 0, "Romanian", ""},
		{19, "ARABIC", 0, "Arabic", ""},
		{20, "BULGARIAN", 0, "Bulgarian", ""},
		{21, "GREEK", 0, "Greek", ""},
		{22, "KOREAN", 0, "Korean", ""},
		{0, NULL, 0, NULL, NULL}};
		
	srna= RNA_def_struct(brna, "UserPreferencesLanguage", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_nested(brna, srna, "UserPreferences");
	RNA_def_struct_ui_text(srna, "Language & Font", "User interface translation settings.");
	
	prop= RNA_def_property(srna, "international_fonts", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transopts", USER_DOTRANSLATE);
	RNA_def_property_ui_text(prop, "International Fonts", "Use international fonts.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "dpi", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "dpi");
	RNA_def_property_range(prop, 48, 128);
	RNA_def_property_ui_text(prop, "DPI", "Font size and resolution for display.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	/* Language Selection */

	prop= RNA_def_property(srna, "language", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, language_items);
	RNA_def_property_ui_text(prop, "Language", "Language use for translation.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "translate_tooltips", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transopts", USER_TR_TOOLTIPS);
	RNA_def_property_ui_text(prop, "Translate Tooltips", "Translate Tooltips.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "translate_buttons", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transopts", USER_TR_BUTTONS);
	RNA_def_property_ui_text(prop, "Translate Buttons", "Translate button labels.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "translate_toolbox", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transopts", USER_TR_MENUS);
	RNA_def_property_ui_text(prop, "Translate Toolbox", "Translate toolbox menu.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);

	prop= RNA_def_property(srna, "use_textured_fonts", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transopts", USER_USETEXTUREFONT);
	RNA_def_property_ui_text(prop, "Textured Fonts", "Use textures for drawing international fonts.");
	RNA_def_property_update(prop, NC_WINDOW, NULL);
}

static void rna_def_userdef_autosave(BlenderRNA *brna)
{
	PropertyRNA *prop;
	StructRNA *srna;

	/* Autosave  */

	srna= RNA_def_struct(brna, "UserPreferencesAutosave", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_nested(brna, srna, "UserPreferences");
	RNA_def_struct_ui_text(srna, "Auto Save", "Automatic backup file settings.");

	prop= RNA_def_property(srna, "save_version", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "versions");
	RNA_def_property_range(prop, 0, 32);
	RNA_def_property_ui_text(prop, "Save Versions", "The number of old versions to maintain in the current directory, when manually saving.");

	prop= RNA_def_property(srna, "auto_save_temporary_files", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_AUTOSAVE);
	RNA_def_property_ui_text(prop, "Auto Save Temporary Files", "Automatic saving of temporary files.");

	prop= RNA_def_property(srna, "auto_save_time", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "savetime");
	RNA_def_property_range(prop, 1, 60);
	RNA_def_property_ui_text(prop, "Auto Save Time", "The time (in minutes) to wait between automatic temporary saves.");

	prop= RNA_def_property(srna, "recent_files", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 0, 30);
	RNA_def_property_ui_text(prop, "Recent Files", "Maximum number of recently opened files to remember.");

	prop= RNA_def_property(srna, "save_preview_images", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_SAVE_PREVIEWS);
	RNA_def_property_ui_text(prop, "Save Preview Images", "Enables automatic saving of preview images in the .blend file.");
}

static void rna_def_userdef_system(BlenderRNA *brna)
{
	PropertyRNA *prop;
	StructRNA *srna;

	static EnumPropertyItem gl_texture_clamp_items[] = {
		{0, "GL_CLAMP_OFF", 0, "GL Texture Clamp Off", ""},
		{8192, "GL_CLAMP_8192", 0, "GL Texture Clamp 8192", ""},
		{4096, "GL_CLAMP_4096", 0, "GL Texture Clamp 4096", ""},
		{2048, "GL_CLAMP_2048", 0, "GL Texture Clamp 2048", ""},
		{1024, "GL_CLAMP_1024", 0, "GL Texture Clamp 1024", ""},
		{512, "GL_CLAMP_512", 0, "GL Texture Clamp 512", ""},
		{256, "GL_CLAMP_256", 0, "GL Texture Clamp 256", ""},
		{128, "GL_CLAMP_128", 0, "GL Texture Clamp 128", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem audio_mixing_samples_items[] = {
		{256, "AUDIO_SAMPLES_256", 0, "256", "Set audio mixing buffer size to 256 samples"},
		{512, "AUDIO_SAMPLES_512", 0, "512", "Set audio mixing buffer size to 512 samples"},
		{1024, "AUDIO_SAMPLES_1024", 0, "1024", "Set audio mixing buffer size to 1024 samples"},
		{2048, "AUDIO_SAMPLES_2048", 0, "2048", "Set audio mixing buffer size to 2048 samples"},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem draw_method_items[] = {
		{USER_DRAW_TRIPLE, "TRIPLE_BUFFER", 0, "Triple Buffer", "Use a third buffer for minimal redraws at the cost of more memory."},
		{USER_DRAW_OVERLAP, "OVERLAP", 0, "Overlap", "Redraw all overlapping regions, minimal memory usage but more redraws."},
		{USER_DRAW_FULL, "FULL", 0, "Full", "Do a full redraw each time, slow, only use for reference or when all else fails."},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "UserPreferencesSystem", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_nested(brna, srna, "UserPreferences");
	RNA_def_struct_ui_text(srna, "System & OpenGL", "Graphics driver and operating system settings.");

	/* System & OpenGL */

	prop= RNA_def_property(srna, "solid_lights", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "light", "");
	RNA_def_property_struct_type(prop, "UserSolidLight");
	RNA_def_property_ui_text(prop, "Solid Lights", "Lights user to display objects in solid draw mode.");

	prop= RNA_def_property(srna, "use_weight_color_range", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_CUSTOM_RANGE);
	RNA_def_property_ui_text(prop, "Use Weight Color Range", "Enable color range used for weight visualization in weight painting mode.");

	prop= RNA_def_property(srna, "weight_color_range", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "coba_weight");
	RNA_def_property_struct_type(prop, "ColorRamp");
	RNA_def_property_ui_text(prop, "Weight Color Range", "Color range used for weight visualization in weight painting mode.");

	prop= RNA_def_property(srna, "enable_all_codecs", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_ALLWINCODECS);
	RNA_def_property_ui_text(prop, "Enable All Codecs", "Enables automatic saving of preview images in the .blend file (Windows only).");

	prop= RNA_def_property(srna, "auto_run_python_scripts", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_DONT_DOSCRIPTLINKS);
	RNA_def_property_ui_text(prop, "Auto Run Python Scripts", "Allow any .blend file to run scripts automatically (unsafe with blend files from an untrusted source).");

	prop= RNA_def_property(srna, "emulate_numpad", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_NONUMPAD);
	RNA_def_property_ui_text(prop, "Emulate Numpad", "Causes the 1 to 0 keys to act as the numpad (useful for laptops).");

	prop= RNA_def_property(srna, "prefetch_frames", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "prefetchframes");
	RNA_def_property_range(prop, 0, 500);
	RNA_def_property_ui_text(prop, "Prefetch Frames", "Number of frames to render ahead during playback.");

	prop= RNA_def_property(srna, "memory_cache_limit", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "memcachelimit");
	RNA_def_property_range(prop, 0, (sizeof(void *) ==8)? 1024*16: 1024); /* 32 bit 2 GB, 64 bit 16 GB */
	RNA_def_property_ui_text(prop, "Memory Cache Limit", "Memory cache limit in sequencer (megabytes).");

	prop= RNA_def_property(srna, "frame_server_port", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "frameserverport");
	RNA_def_property_range(prop, 0, 32727);
	RNA_def_property_ui_text(prop, "Frame Server Port", "Frameserver Port for Framserver-Rendering.");

	prop= RNA_def_property(srna, "game_sound", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "gameflags", USER_DISABLE_SOUND);
	RNA_def_property_ui_text(prop, "Game Sound", "Enables sounds to be played in games.");

	prop= RNA_def_property(srna, "filter_file_extensions", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_FILTERFILEEXTS);
	RNA_def_property_ui_text(prop, "Filter File Extensions", "Display only files with extensions in the image select window.");

	prop= RNA_def_property(srna, "hide_dot_files_datablocks", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "uiflag", USER_HIDE_DOT);
	RNA_def_property_ui_text(prop, "Hide Dot Files/Datablocks", "Hide files/datablocks that start with a dot(.*)");

	prop= RNA_def_property(srna, "clip_alpha", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "glalphaclip");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Clip Alpha", "Clip alpha below this threshold in the 3d textured view.");
	
	prop= RNA_def_property(srna, "use_mipmaps", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "gameflags", USER_DISABLE_MIPMAP);
	RNA_def_property_ui_text(prop, "Mipmaps", "Scale textures for the 3d View (looks nicer but uses more memory and slows image reloading.)");

	prop= RNA_def_property(srna, "gl_texture_limit", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "glreslimit");
	RNA_def_property_enum_items(prop, gl_texture_clamp_items);
	RNA_def_property_ui_text(prop, "GL Texture Limit", "Limit the texture size to save graphics memory.");

	prop= RNA_def_property(srna, "texture_time_out", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "textimeout");
	RNA_def_property_range(prop, 0, 3600);
	RNA_def_property_ui_text(prop, "Texture Time Out", "Time since last access of a GL texture in seconds after which it is freed. (Set to 0 to keep textures allocated.)");

	prop= RNA_def_property(srna, "texture_collection_rate", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "texcollectrate");
	RNA_def_property_range(prop, 1, 3600);
	RNA_def_property_ui_text(prop, "Texture Collection Rate", "Number of seconds between each run of the GL texture garbage collector.");

	prop= RNA_def_property(srna, "window_draw_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "wmdrawmethod");
	RNA_def_property_enum_items(prop, draw_method_items);
	RNA_def_property_ui_text(prop, "Window Draw Method", "Drawing method used by the window manager.");

	prop= RNA_def_property(srna, "audio_mixing_buffer", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mixbufsize");
	RNA_def_property_enum_items(prop, audio_mixing_samples_items);
	RNA_def_property_ui_text(prop, "Audio Mixing Buffer", "Sets the number of samples used by the audio mixing buffer.");

#if 0
	prop= RNA_def_property(srna, "verse_master", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "versemaster");
	RNA_def_property_ui_text(prop, "Verse Master", "The Verse Master-server IP");

	prop= RNA_def_property(srna, "verse_username", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "verseuser");
	RNA_def_property_ui_text(prop, "Verse Username", "The Verse user name");
#endif
}

static void rna_def_userdef_filepaths(BlenderRNA *brna)
{
	PropertyRNA *prop;
	StructRNA *srna;
	
	srna= RNA_def_struct(brna, "UserPreferencesFilePaths", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_nested(brna, srna, "UserPreferences");
	RNA_def_struct_ui_text(srna, "File Paths", "Default paths for external files.");

	prop= RNA_def_property(srna, "use_relative_paths", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_RELPATHS);
	RNA_def_property_ui_text(prop, "Relative Paths", "Default relative path option for the file selector.");

	prop= RNA_def_property(srna, "compress_file", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", USER_FILECOMPRESS);
	RNA_def_property_ui_text(prop, "Compress File", "Enable file compression when saving .blend files.");

	prop= RNA_def_property(srna, "fonts_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "fontdir");
	RNA_def_property_ui_text(prop, "Fonts Directory", "The default directory to search for loading fonts.");

	prop= RNA_def_property(srna, "textures_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "textudir");
	RNA_def_property_ui_text(prop, "Textures Directory", "The default directory to search for textures.");

	prop= RNA_def_property(srna, "texture_plugin_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "plugtexdir");
	RNA_def_property_ui_text(prop, "Texture Plugin Directory", "The default directory to search for texture plugins.");

	prop= RNA_def_property(srna, "sequence_plugin_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "plugseqdir");
	RNA_def_property_ui_text(prop, "Sequence Plugin Directory", "The default directory to search for sequence plugins.");

	prop= RNA_def_property(srna, "render_output_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "renderdir");
	RNA_def_property_ui_text(prop, "Render Output Directory", "The default directory for rendering output.");

	prop= RNA_def_property(srna, "python_scripts_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "pythondir");
	RNA_def_property_ui_text(prop, "Python Scripts Directory", "The default directory to search for Python scripts (resets python module search path: sys.path).");

	prop= RNA_def_property(srna, "sounds_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "sounddir");
	RNA_def_property_ui_text(prop, "Sounds Directory", "The default directory to search for sounds.");

	prop= RNA_def_property(srna, "temporary_directory", PROP_STRING, PROP_DIRPATH);
	RNA_def_property_string_sdna(prop, NULL, "tempdir");
	RNA_def_property_ui_text(prop, "Temporary Directory", "The directory for storing temporary save files.");
}

void RNA_def_userdef(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem user_pref_sections[] = {
		{0, "VIEW_CONTROLS", 0, "View & Controls", ""},
		{1, "EDIT_METHODS", 0, "Edit Methods", ""},
		{2, "LANGUAGE_COLORS", 0, "Language & Colors", ""},
		{3, "AUTO_SAVE", 0, "Auto Save", ""},
		{4, "SYSTEM_OPENGL", 0, "System & OpenGL", ""},
		{5, "FILE_PATHS", 0, "File Paths", ""},
		{6, "THEMES", 0, "Themes", ""},
		{0, NULL, 0, NULL, NULL}};

	rna_def_userdef_dothemes(brna);
	rna_def_userdef_solidlight(brna);

	srna= RNA_def_struct(brna, "UserPreferences", NULL);
	RNA_def_struct_sdna(srna, "UserDef");
	RNA_def_struct_ui_text(srna, "User Preferences", "Global user preferences.");

	prop= RNA_def_property(srna, "active_section", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "userpref");
	RNA_def_property_enum_items(prop, user_pref_sections);
	RNA_def_property_ui_text(prop, "Active Section", "Active section of the user preferences shown in the user interface.");

	prop= RNA_def_property(srna, "themes", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "themes", NULL);
	RNA_def_property_struct_type(prop, "Theme");
	RNA_def_property_ui_text(prop, "Themes", "");

	prop= RNA_def_property(srna, "uistyles", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "uistyles", NULL);
	RNA_def_property_struct_type(prop, "ThemeStyle");
	RNA_def_property_ui_text(prop, "Styles", "");
	
	/* nested structs */
	prop= RNA_def_property(srna, "view", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "UserPreferencesView");
	RNA_def_property_pointer_funcs(prop, "rna_UserDef_view_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "View & Controls", "Preferences related to viewing data.");

	prop= RNA_def_property(srna, "edit", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "UserPreferencesEdit");
	RNA_def_property_pointer_funcs(prop, "rna_UserDef_edit_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Edit Methods", "Settings for interacting with Blender data.");
	
	prop= RNA_def_property(srna, "autosave", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "UserPreferencesAutosave");
	RNA_def_property_pointer_funcs(prop, "rna_UserDef_autosave_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Auto Save", "Automatic backup file settings.");

	prop= RNA_def_property(srna, "language", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "UserPreferencesLanguage");
	RNA_def_property_pointer_funcs(prop, "rna_UserDef_language_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Language & Font", "User interface translation settings.");
	
	prop= RNA_def_property(srna, "filepaths", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "UserPreferencesFilePaths");
	RNA_def_property_pointer_funcs(prop, "rna_UserDef_filepaths_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "File Paths", "Default paths for external files.");
	
	prop= RNA_def_property(srna, "system", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "UserPreferencesSystem");
	RNA_def_property_pointer_funcs(prop, "rna_UserDef_system_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "System & OpenGL", "Graphics driver and operating system settings.");
	
	rna_def_userdef_view(brna);
	rna_def_userdef_edit(brna);
	rna_def_userdef_autosave(brna);
	rna_def_userdef_language(brna);
	rna_def_userdef_filepaths(brna);
	rna_def_userdef_system(brna);
	
}

#endif

