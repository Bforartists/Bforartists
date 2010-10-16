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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

#include "RNA_define.h"
#include "RNA_access.h"
#include "RNA_enum_types.h"

#include "BKE_utildefines.h"

#ifdef RNA_RUNTIME

#include "BKE_main.h"
#include "BKE_curve.h"
#include "BKE_mesh.h"
#include "BKE_armature.h"
#include "BKE_library.h"
#include "BKE_object.h"
#include "BKE_material.h"
#include "BKE_image.h"
#include "BKE_texture.h"
#include "BKE_scene.h"
#include "BKE_text.h"
#include "BKE_action.h"
#include "BKE_group.h"
#include "BKE_brush.h"
#include "BKE_lattice.h"
#include "BKE_mball.h"
#include "BKE_world.h"
#include "BKE_particle.h"
#include "BKE_font.h"
#include "BKE_node.h"

#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_text_types.h"
#include "DNA_texture_types.h"
#include "DNA_group_types.h"
#include "DNA_brush_types.h"
#include "DNA_lattice_types.h"
#include "DNA_meta_types.h"
#include "DNA_world_types.h"
#include "DNA_particle_types.h"
#include "DNA_vfont_types.h"
#include "DNA_node_types.h"

#include "ED_screen.h"

Tex *rna_Main_add_texture(Main *bmain, char *name)
{
	return add_texture(name);
}

Camera *rna_Main_cameras_new(Main *bmain, char* name)
{
	ID *id= add_camera(name);
	id->us--;
	return (Camera *)id;
}
void rna_Main_cameras_remove(Main *bmain, ReportList *reports, struct Camera *camera)
{
	if(ID_REAL_USERS(camera) <= 0)
		free_libblock(&bmain->camera, camera);
	else
		BKE_reportf(reports, RPT_ERROR, "Camera \"%s\" must have zero users to be removed, found %d.", camera->id.name+2, ID_REAL_USERS(camera));

	/* XXX python now has invalid pointer? */
}

Scene *rna_Main_scenes_new(Main *bmain, char* name)
{
	return add_scene(name);
}
void rna_Main_scenes_remove(Main *bmain, bContext *C, ReportList *reports, struct Scene *scene)
{
	/* dont call free_libblock(...) directly */
	Scene *newscene;

	if(scene->id.prev)
		newscene= scene->id.prev;
	else if(scene->id.next)
		newscene= scene->id.next;
	else {
		BKE_reportf(reports, RPT_ERROR, "Scene \"%s\" is the last, cant ve removed.", scene->id.name+2);
		return;
	}

	ED_screen_set_scene(C, newscene);

	unlink_scene(bmain, scene, newscene);
}

Object *rna_Main_objects_new(Main *bmain, ReportList *reports, char* name, ID *data)
{
	Object *ob;
	int type= OB_EMPTY;
	if(data) {
		switch(GS(data->name)) {
			case ID_ME:
				type= OB_MESH;
				break;
			case ID_CU:
				type= curve_type((struct Curve *)data);
				break;
			case ID_MB:
				type= OB_MBALL;
				break;
			case ID_LA:
				type= OB_LAMP;
				break;
			case ID_CA:
				type= OB_CAMERA;
				break;
			case ID_LT:
				type= OB_LATTICE;
				break;
			case ID_AR:
				type= OB_ARMATURE;
				break;
			default:
			{
				const char *idname;
				if(RNA_enum_id_from_value(id_type_items, GS(data->name), &idname) == 0)
					idname= "UNKNOWN";

				BKE_reportf(reports, RPT_ERROR, "ID type '%s' is not valid for a object.", idname);
				return NULL;
			}
		}

		data->us++;
	}

	ob= add_only_object(type, name);
	ob->id.us--;

	ob->data= data;
	test_object_materials(ob->data);
	
	return ob;
}

void rna_Main_objects_remove(Main *bmain, ReportList *reports, struct Object *object)
{
	if(ID_REAL_USERS(object) <= 0) {
		unlink_object(object); /* needed or ID pointers to this are not cleared */
		free_libblock(&bmain->object, object);
	}
	else {
		BKE_reportf(reports, RPT_ERROR, "Object \"%s\" must have zero users to be removed, found %d.", object->id.name+2, ID_REAL_USERS(object));
	}
}

struct Material *rna_Main_materials_new(Main *bmain, char* name)
{
	ID *id= (ID *)add_material(name);
	id->us--;
	return (Material *)id;
}
void rna_Main_materials_remove(Main *bmain, ReportList *reports, struct Material *material)
{
	if(ID_REAL_USERS(material) <= 0)
		free_libblock(&bmain->mat, material);
	else
		BKE_reportf(reports, RPT_ERROR, "Material \"%s\" must have zero users to be removed, found %d.", material->id.name+2, ID_REAL_USERS(material));

	/* XXX python now has invalid pointer? */
}

// XXX, commended for now, need to see how this can be used with node groups.
struct bNodeTree *rna_Main_nodetree_new(Main *bmain, int type)
{
	bNodeTree *tree = ntreeAddTree(type);
	tree->id.us--;
	return tree;
}
void rna_Main_nodetree_remove(Main *bmain, ReportList *reports, struct bNodeTree *tree)
{
	if(ID_REAL_USERS(tree) <= 0)
		free_libblock(&bmain->nodetree, tree);
	else
		BKE_reportf(reports, RPT_ERROR, "Node Tree \"%s\" must have zero users to be removed, found %d.", tree->id.name+2, ID_REAL_USERS(tree));

	/* XXX python now has invalid pointer? */
}

Mesh *rna_Main_meshes_new(Main *bmain, char* name)
{
	Mesh *me= add_mesh(name);
	me->id.us--;
	return me;
}
void rna_Main_meshes_remove(Main *bmain, ReportList *reports, Mesh *mesh)
{
	if(ID_REAL_USERS(mesh) <= 0)
		free_libblock(&bmain->mesh, mesh);
	else
		BKE_reportf(reports, RPT_ERROR, "Mesh \"%s\" must have zero users to be removed, found %d.", mesh->id.name+2, ID_REAL_USERS(mesh));

	/* XXX python now has invalid pointer? */
}

Lamp *rna_Main_lamps_new(Main *bmain, char* name)
{
	Lamp *lamp= add_lamp(name);
	lamp->id.us--;
	return lamp;
}
void rna_Main_lamps_remove(Main *bmain, ReportList *reports, Lamp *lamp)
{
	if(ID_REAL_USERS(lamp) <= 0)
		free_libblock(&bmain->lamp, lamp);
	else
		BKE_reportf(reports, RPT_ERROR, "Lamp \"%s\" must have zero users to be removed, found %d.", lamp->id.name+2, ID_REAL_USERS(lamp));

	/* XXX python now has invalid pointer? */
}

Image *rna_Main_images_new(Main *bmain, char* name, int width, int height, int alpha, int float_buffer)
{
	float color[4]= {0.0, 0.0, 0.0, 1.0};
	Image *image= BKE_add_image_size(width, height, name, alpha ? 32:24, float_buffer, 0, color);
	image->id.us--;
	return image;
}
Image *rna_Main_images_load(Main *bmain, ReportList *reports, char *filepath)
{
	Image *ima;

	errno= 0;
	ima= BKE_add_image_file(filepath);

	if(!ima)
		BKE_reportf(reports, RPT_ERROR, "Can't read: \"%s\", %s.", filepath, errno ? strerror(errno) : "Unsupported image format");

	return ima;
}
void rna_Main_images_remove(Main *bmain, ReportList *reports, Image *image)
{
	if(ID_REAL_USERS(image) <= 0)
		free_libblock(&bmain->image, image);
	else
		BKE_reportf(reports, RPT_ERROR, "Image \"%s\" must have zero users to be removed, found %d.", image->id.name+2, ID_REAL_USERS(image));

	/* XXX python now has invalid pointer? */
}

Lattice *rna_Main_lattices_new(Main *bmain, char* name)
{
	Lattice *lt= add_lattice(name);
	lt->id.us--;
	return lt;
}
void rna_Main_lattices_remove(Main *bmain, ReportList *reports, struct Lattice *lt)
{
	if(ID_REAL_USERS(lt) <= 0)
		free_libblock(&bmain->latt, lt);
	else
		BKE_reportf(reports, RPT_ERROR, "Lattice \"%s\" must have zero users to be removed, found %d.", lt->id.name+2, ID_REAL_USERS(lt));
}

Curve *rna_Main_curves_new(Main *bmain, char* name, int type)
{
	Curve *cu= add_curve(name, type);
	cu->id.us--;
	return cu;
}
void rna_Main_curves_remove(Main *bmain, ReportList *reports, struct Curve *cu)
{
	if(ID_REAL_USERS(cu) <= 0)
		free_libblock(&bmain->curve, cu);
	else
		BKE_reportf(reports, RPT_ERROR, "Curve \"%s\" must have zero users to be removed, found %d.", cu->id.name+2, ID_REAL_USERS(cu));
}

MetaBall *rna_Main_metaballs_new(Main *bmain, char* name)
{
	MetaBall *mb= add_mball(name);
	mb->id.us--;
	return mb;
}
void rna_Main_metaballs_remove(Main *bmain, ReportList *reports, struct MetaBall *mb)
{
	if(ID_REAL_USERS(mb) <= 0)
		free_libblock(&bmain->mball, mb);
	else
		BKE_reportf(reports, RPT_ERROR, "MetaBall \"%s\" must have zero users to be removed, found %d.", mb->id.name+2, ID_REAL_USERS(mb));
}

VFont *rna_Main_fonts_load(Main *bmain, ReportList *reports, char *filepath)
{
	VFont *font;

	errno= 0;
	font= load_vfont(filepath);

	if(!font)
		BKE_reportf(reports, RPT_ERROR, "Can't read: \"%s\", %s.", filepath, errno ? strerror(errno) : "Unsupported font format");

	return font;

}
void rna_Main_fonts_remove(Main *bmain, ReportList *reports, VFont *vfont)
{
	if(ID_REAL_USERS(vfont) <= 0)
		free_libblock(&bmain->vfont, vfont);
	else
		BKE_reportf(reports, RPT_ERROR, "Font \"%s\" must have zero users to be removed, found %d.", vfont->id.name+2, ID_REAL_USERS(vfont));

	/* XXX python now has invalid pointer? */
}

Tex *rna_Main_textures_new(Main *bmain, char* name, int type)
{
	Tex *tex= add_texture(name);
	tex_set_type(tex, type);
	tex->id.us--;
	return tex;
}
void rna_Main_textures_remove(Main *bmain, ReportList *reports, struct Tex *tex)
{
	if(ID_REAL_USERS(tex) <= 0)
		free_libblock(&bmain->tex, tex);
	else
		BKE_reportf(reports, RPT_ERROR, "Texture \"%s\" must have zero users to be removed, found %d.", tex->id.name+2, ID_REAL_USERS(tex));
}

Brush *rna_Main_brushes_new(Main *bmain, char* name)
{
	Brush *brush = add_brush(name);
	brush->id.us--;
	return brush;
}
void rna_Main_brushes_remove(Main *bmain, ReportList *reports, struct Brush *brush)
{
	if(ID_REAL_USERS(brush) <= 0)
		free_libblock(&bmain->brush, brush);
	else
		BKE_reportf(reports, RPT_ERROR, "Brush \"%s\" must have zero users to be removed, found %d.", brush->id.name+2, ID_REAL_USERS(brush));
}

World *rna_Main_worlds_new(Main *bmain, char* name)
{
	World *world = add_world(name);
	world->id.us--;
	return world;
}
void rna_Main_worlds_remove(Main *bmain, ReportList *reports, struct World *world)
{
	if(ID_REAL_USERS(world) <= 0)
		free_libblock(&bmain->world, world);
	else
		BKE_reportf(reports, RPT_ERROR, "World \"%s\" must have zero users to be removed, found %d.", world->id.name+2, ID_REAL_USERS(world));
}

Group *rna_Main_groups_new(Main *bmain, char* name)
{
	return add_group(name);
}
void rna_Main_groups_remove(Main *bmain, ReportList *reports, Group *group)
{
	unlink_group(group);
	free_libblock(&bmain->group, group);
	/* XXX python now has invalid pointer? */
}

Text *rna_Main_texts_new(Main *bmain, char* name)
{
	return add_empty_text(name);
}
void rna_Main_texts_remove(Main *bmain, ReportList *reports, Text *text)
{
	unlink_text(bmain, text);
	free_libblock(&bmain->text, text);
	/* XXX python now has invalid pointer? */
}

Text *rna_Main_texts_load(Main *bmain, ReportList *reports, char* filepath)
{
	Text *txt;

	errno= 0;
	txt= add_text(filepath, bmain->name);

	if(!txt)
		BKE_reportf(reports, RPT_ERROR, "Can't read: \"%s\", %s.", filepath, errno ? strerror(errno) : "Unable to load text");

	return txt;
}

bArmature *rna_Main_armatures_new(Main *bmain, char* name)
{
	bArmature *arm= add_armature(name);
	arm->id.us--;
	return arm;
}
void rna_Main_armatures_remove(Main *bmain, ReportList *reports, bArmature *arm)
{
	if(ID_REAL_USERS(arm) <= 0)
		free_libblock(&bmain->armature, arm);
	else
		BKE_reportf(reports, RPT_ERROR, "Armature \"%s\" must have zero users to be removed, found %d.", arm->id.name+2, ID_REAL_USERS(arm));

	/* XXX python now has invalid pointer? */
}

bAction *rna_Main_actions_new(Main *bmain, char* name)
{
	bAction *act= add_empty_action(name);
	act->id.us--;
	act->id.flag &= ~LIB_FAKEUSER;
	return act;
}
void rna_Main_actions_remove(Main *bmain, ReportList *reports, bAction *act)
{
	if(ID_REAL_USERS(act) <= 0)
		free_libblock(&bmain->action, act);
	else
		BKE_reportf(reports, RPT_ERROR, "Action \"%s\" must have zero users to be removed, found %d.", act->id.name+2, ID_REAL_USERS(act));

	/* XXX python now has invalid pointer? */
}

ParticleSettings *rna_Main_particles_new(Main *bmain, char* name)
{
	ParticleSettings *part = psys_new_settings(name, bmain);
	part->id.us--;
	return part;
}
void rna_Main_particles_remove(Main *bmain, ReportList *reports, ParticleSettings *part)
{
	if(ID_REAL_USERS(part) <= 0)
		free_libblock(&bmain->particle, part);
	else
		BKE_reportf(reports, RPT_ERROR, "Particle Settings \"%s\" must have zero users to be removed, found %d.", part->id.name+2, ID_REAL_USERS(part));

	/* XXX python now has invalid pointer? */
}

#else

void RNA_api_main(StructRNA *srna)
{
	/*
	FunctionRNA *func;
	PropertyRNA *parm;
	*/
	/* maybe we want to add functions in 'bpy.data' still?
	 * for now they are all in collections bpy.data.images.new(...) */
	/*
	func= RNA_def_function(srna, "add_image", "rna_Main_add_image");
	RNA_def_function_ui_description(func, "Add a new image.");
	parm= RNA_def_string(func, "filepath", "", 0, "", "File path to load image from.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_pointer(func, "image", "Image", "", "New image.");
	RNA_def_function_return(func, parm);
	*/

}

void RNA_def_main_cameras(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainCameras");
	srna= RNA_def_struct(brna, "MainCameras", NULL);
	RNA_def_struct_ui_text(srna, "Main Cameras", "Collection of cameras");

	func= RNA_def_function(srna, "new", "rna_Main_cameras_new");
	RNA_def_function_ui_description(func, "Add a new camera to the main database");
	parm= RNA_def_string(func, "name", "Camera", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "camera", "Camera", "", "New camera datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_cameras_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a camera from the current blendfile.");
	parm= RNA_def_pointer(func, "camera", "Camera", "", "Camera to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}

void RNA_def_main_scenes(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainScenes");
	srna= RNA_def_struct(brna, "MainScenes", NULL);
	RNA_def_struct_ui_text(srna, "Main Scenes", "Collection of scenes");

	func= RNA_def_function(srna, "new", "rna_Main_scenes_new");
	RNA_def_function_ui_description(func, "Add a new scene to the main database");
	parm= RNA_def_string(func, "name", "Scene", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "scene", "Scene", "", "New scene datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_scenes_remove");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a scene from the current blendfile.");
	parm= RNA_def_pointer(func, "scene", "Scene", "", "Scene to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}

void RNA_def_main_objects(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainObjects");
	srna= RNA_def_struct(brna, "MainObjects", NULL);
	RNA_def_struct_ui_text(srna, "Main Objects", "Collection of objects");

	func= RNA_def_function(srna, "new", "rna_Main_objects_new");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Add a new object to the main database");
	parm= RNA_def_string(func, "name", "Object", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_pointer(func, "object_data", "ID", "", "Object data or None for an empty object.");
	RNA_def_property_flag(parm, PROP_REQUIRED);

	/* return type */
	parm= RNA_def_pointer(func, "object", "Object", "", "New object datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_objects_remove");
	RNA_def_function_ui_description(func, "Remove a object from the current blendfile.");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	parm= RNA_def_pointer(func, "object", "Object", "", "Object to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}

void RNA_def_main_materials(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainMaterials");
	srna= RNA_def_struct(brna, "MainMaterials", NULL);
	RNA_def_struct_ui_text(srna, "Main Material", "Collection of materials");

	func= RNA_def_function(srna, "new", "rna_Main_materials_new");
	RNA_def_function_ui_description(func, "Add a new material to the main database");
	parm= RNA_def_string(func, "name", "Material", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "material", "Material", "", "New material datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_materials_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a material from the current blendfile.");
	parm= RNA_def_pointer(func, "material", "Material", "", "Material to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_node_groups(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
//	FunctionRNA *func;
//	PropertyRNA *parm;

/*	static EnumPropertyItem node_nodetree_items[] = {
	{0, "SHADER",       0,    "Shader",       ""},
	{1, "COMPOSITE",    0,    "Composite",    ""},
	{2, "TEXTURE",      0,    "Texture",      ""},
	{0, NULL, 0, NULL, NULL}}; */

	RNA_def_property_srna(cprop, "MainNodeTrees");
	srna= RNA_def_struct(brna, "MainNodeTrees", NULL);
	RNA_def_struct_ui_text(srna, "Main Node Trees", "Collection of node trees");

#if 0 // need to see some examples of using these functions before enabling.
	func= RNA_def_function(srna, "new", "rna_Main_nodetree_new");
	RNA_def_function_ui_description(func, "Add a new node tree to the main database");
	parm= RNA_def_enum(func, "type", node_nodetree_items, 0, "Type", "The type of curve object to add");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "tree", "NodeTree", "", "New node tree datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_nodetree_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a node tree from the current blendfile.");
	parm= RNA_def_pointer(func, "tree", "NodeTree", "", "Node tree to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
#endif
}
void RNA_def_main_meshes(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainMeshes");
	srna= RNA_def_struct(brna, "MainMeshes", NULL);
	RNA_def_struct_ui_text(srna, "Main Meshes", "Collection of meshes");

	func= RNA_def_function(srna, "new", "rna_Main_meshes_new");
	RNA_def_function_ui_description(func, "Add a new mesh to the main database");
	parm= RNA_def_string(func, "name", "Mesh", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "New mesh datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_meshes_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a mesh from the current blendfile.");
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "Mesh to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_lamps(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainLamps");
	srna= RNA_def_struct(brna, "MainLamps", NULL);
	RNA_def_struct_ui_text(srna, "Main Lamps", "Collection of lamps");

	func= RNA_def_function(srna, "new", "rna_Main_lamps_new");
	RNA_def_function_ui_description(func, "Add a new lamp to the main database");
	parm= RNA_def_string(func, "name", "Lamp", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "lamp", "Lamp", "", "New lamp datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_lamps_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a lamp from the current blendfile.");
	parm= RNA_def_pointer(func, "lamp", "Lamp", "", "Lamp to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_libraries(BlenderRNA *brna, PropertyRNA *cprop)
{

}
void RNA_def_main_screens(BlenderRNA *brna, PropertyRNA *cprop)
{

}
void RNA_def_main_window_managers(BlenderRNA *brna, PropertyRNA *cprop)
{
    
}
void RNA_def_main_images(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainImages");
	srna= RNA_def_struct(brna, "MainImages", NULL);
	RNA_def_struct_ui_text(srna, "Main Images", "Collection of images");

	func= RNA_def_function(srna, "new", "rna_Main_images_new");
	RNA_def_function_ui_description(func, "Add a new image to the main database");
	parm= RNA_def_string(func, "name", "Image", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_int(func, "width", 1024, 1, INT_MAX, "", "Width of the image.", 0, INT_MAX);
	parm= RNA_def_int(func, "height", 1024, 1, INT_MAX, "", "Height of the image.", 0, INT_MAX);
	parm= RNA_def_boolean(func, "alpha", 0, "Alpha", "Use alpha channel");
	parm= RNA_def_boolean(func, "float_buffer", 0, "Float Buffer", "Create an image with floating point color");
	/* return type */
	parm= RNA_def_pointer(func, "image", "Image", "", "New image datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "load", "rna_Main_images_load");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Load a new image into the main database");
	parm= RNA_def_string(func, "filepath", "File Path", 0, "", "path of the file to load.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "image", "Image", "", "New image datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_images_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove an image from the current blendfile.");
	parm= RNA_def_pointer(func, "image", "Image", "", "Image to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}

void RNA_def_main_lattices(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainLattices");
	srna= RNA_def_struct(brna, "MainLattices", NULL);
	RNA_def_struct_ui_text(srna, "Main Lattices", "Collection of lattices");

	func= RNA_def_function(srna, "new", "rna_Main_lattices_new");
	RNA_def_function_ui_description(func, "Add a new lattice to the main database");
	parm= RNA_def_string(func, "name", "Lattice", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "lattice", "Lattice", "", "New lattices datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_lattices_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a lattice from the current blendfile.");
	parm= RNA_def_pointer(func, "lattice", "Lattice", "", "Lattice to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_curves(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainCurves");
	srna= RNA_def_struct(brna, "MainCurves", NULL);
	RNA_def_struct_ui_text(srna, "Main Curves", "Collection of curves");

	func= RNA_def_function(srna, "new", "rna_Main_curves_new");
	RNA_def_function_ui_description(func, "Add a new curve to the main database");
	parm= RNA_def_string(func, "name", "Curve", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_enum(func, "type", object_type_curve_items, 0, "Type", "The type of curve to add");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "curve", "Curve", "", "New curve datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_curves_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a curve from the current blendfile.");
	parm= RNA_def_pointer(func, "curve", "Curve", "", "Curve to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_metaballs(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainMetaBalls");
	srna= RNA_def_struct(brna, "MainMetaBalls", NULL);
	RNA_def_struct_ui_text(srna, "Main MetaBall", "Collection of metaballs");

	func= RNA_def_function(srna, "new", "rna_Main_metaballs_new");
	RNA_def_function_ui_description(func, "Add a new metaball to the main database");
	parm= RNA_def_string(func, "name", "MetaBall", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "metaball", "MetaBall", "", "New metaball datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_metaballs_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a metaball from the current blendfile.");
	parm= RNA_def_pointer(func, "metaball", "MetaBall", "", "MetaBall to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_fonts(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainFonts");
	srna= RNA_def_struct(brna, "MainFonts", NULL);
	RNA_def_struct_ui_text(srna, "Main Fonts", "Collection of fonts");

	func= RNA_def_function(srna, "load", "rna_Main_fonts_load");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Load a new font into the main database");
	parm= RNA_def_string(func, "filepath", "File Path", 0, "", "path of the font to load.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "vfont", "VectorFont", "", "New font datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_fonts_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a font from the current blendfile.");
	parm= RNA_def_pointer(func, "vfont", "VectorFont", "", "Font to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_textures(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainTextures");
	srna= RNA_def_struct(brna, "MainTextures", NULL);
	RNA_def_struct_ui_text(srna, "Main Textures", "Collection of groups");

	func= RNA_def_function(srna, "new", "rna_Main_textures_new");
	RNA_def_function_ui_description(func, "Add a new texture to the main database");
	parm= RNA_def_string(func, "name", "Texture", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_enum(func, "type", texture_type_items, 0, "Type", "The type of texture to add");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "texture", "Texture", "", "New texture datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_textures_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a texture from the current blendfile.");
	parm= RNA_def_pointer(func, "texture", "Texture", "", "Texture to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_brushes(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainBrushes");
	srna= RNA_def_struct(brna, "MainBrushes", NULL);
	RNA_def_struct_ui_text(srna, "Main Brushes", "Collection of brushes");

	func= RNA_def_function(srna, "new", "rna_Main_brushes_new");
	RNA_def_function_ui_description(func, "Add a new brush to the main database");
	parm= RNA_def_string(func, "name", "Brush", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "brush", "Brush", "", "New brush datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_brushes_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a brush from the current blendfile.");
	parm= RNA_def_pointer(func, "brush", "Brush", "", "Brush to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}

void RNA_def_main_worlds(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainWorlds");
	srna= RNA_def_struct(brna, "MainWorlds", NULL);
	RNA_def_struct_ui_text(srna, "Main Worlds", "Collection of worlds");

	func= RNA_def_function(srna, "new", "rna_Main_worlds_new");
	RNA_def_function_ui_description(func, "Add a new world to the main database");
	parm= RNA_def_string(func, "name", "World", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "world", "World", "", "New world datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_worlds_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a world from the current blendfile.");
	parm= RNA_def_pointer(func, "world", "World", "", "World to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}

void RNA_def_main_groups(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainGroups");
	srna= RNA_def_struct(brna, "MainGroups", NULL);
	RNA_def_struct_ui_text(srna, "Main Groups", "Collection of groups");

	func= RNA_def_function(srna, "new", "rna_Main_groups_new");
	RNA_def_function_ui_description(func, "Add a new group to the main database");
	parm= RNA_def_string(func, "name", "Group", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "group", "Group", "", "New group datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_groups_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a group from the current blendfile.");
	parm= RNA_def_pointer(func, "group", "Group", "", "Group to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_texts(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainTexts");
	srna= RNA_def_struct(brna, "MainTexts", NULL);
	RNA_def_struct_ui_text(srna, "Main Texts", "Collection of texts");

	func= RNA_def_function(srna, "new", "rna_Main_texts_new");
	RNA_def_function_ui_description(func, "Add a new text to the main database");
	parm= RNA_def_string(func, "name", "Text", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "text", "Text", "", "New text datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_texts_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a text from the current blendfile.");
	parm= RNA_def_pointer(func, "text", "Text", "", "Text to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);

	/* load func */
	func= RNA_def_function(srna, "load", "rna_Main_texts_load");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Add a new text to the main database from a file");
	parm= RNA_def_string(func, "filepath", "Path", FILE_MAXDIR + FILE_MAXFILE, "", "path for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "text", "Text", "", "New text datablock.");
	RNA_def_function_return(func, parm);
}
void RNA_def_main_sounds(BlenderRNA *brna, PropertyRNA *cprop)
{

}
void RNA_def_main_armatures(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainArmatures");
	srna= RNA_def_struct(brna, "MainArmatures", NULL);
	RNA_def_struct_ui_text(srna, "Main Armatures", "Collection of armatures");

	func= RNA_def_function(srna, "new", "rna_Main_armatures_new");
	RNA_def_function_ui_description(func, "Add a new armature to the main database");
	parm= RNA_def_string(func, "name", "Armature", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "armature", "Armature", "", "New armature datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_armatures_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a armature from the current blendfile.");
	parm= RNA_def_pointer(func, "armature", "Armature", "", "Armature to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_actions(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainActions");
	srna= RNA_def_struct(brna, "MainActions", NULL);
	RNA_def_struct_ui_text(srna, "Main Actions", "Collection of actions");

	func= RNA_def_function(srna, "new", "rna_Main_actions_new");
	RNA_def_function_ui_description(func, "Add a new action to the main database");
	parm= RNA_def_string(func, "name", "Action", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "action", "Action", "", "New action datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_actions_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a action from the current blendfile.");
	parm= RNA_def_pointer(func, "action", "Action", "", "Action to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_particles(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "MainParticles");
	srna= RNA_def_struct(brna, "MainParticles", NULL);
	RNA_def_struct_ui_text(srna, "Main Particle Settings", "Collection of particle settings");

	func= RNA_def_function(srna, "new", "rna_Main_particles_new");
	RNA_def_function_ui_description(func, "Add a new particle settings instance to the main database");
	parm= RNA_def_string(func, "name", "ParticleSettings", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	/* return type */
	parm= RNA_def_pointer(func, "particle", "ParticleSettings", "", "New particle settings datablock.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove", "rna_Main_particles_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a particle settings instance from the current blendfile.");
	parm= RNA_def_pointer(func, "particle", "ParticleSettings", "", "Particle Settings to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED|PROP_NEVER_NULL);
}
void RNA_def_main_gpencil(BlenderRNA *brna, PropertyRNA *cprop)
{

}

#endif

