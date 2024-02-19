# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from math import radians, degrees

# -----------------------------------------------------------------------------
# utility functions

def mu_assign_material_slots(object, material_list):
    """Given an object and a list of material names removes all material slots from the object
       adds new ones for each material in the material list, adds the materials to the slots as well."""

    scene = bpy.context.scene
    active_object = bpy.context.active_object
    bpy.context.view_layer.objects.active = object

    for _ in range(len(object.material_slots)):
        bpy.ops.object.material_slot_remove()

    # re-add them and assign material
    i = 0
    for mat in material_list:
        material = bpy.data.materials[mat]
        object.data.materials.append(material)
        i += 1

    # restore active object:
    bpy.context.view_layer.objects.active = active_object

def mu_assign_to_data(object, material, index, edit_mode, all = True):
    """Assign the material to the object data (polygons/splines)"""

    if object.type == 'MESH':
        # now assign the material to the mesh
        mesh = object.data
        if all:
            for poly in mesh.polygons:
                poly.material_index = index
        else:
            for poly in mesh.polygons:
                if poly.select:
                    poly.material_index = index

        mesh.update()

    elif object.type in {'CURVE', 'SURFACE', 'TEXT'}:
        bpy.ops.object.mode_set(mode = 'EDIT')    # This only works in Edit mode

        # If operator was run in Object mode
        if not edit_mode:
            # Select everything in Edit mode
            bpy.ops.curve.select_all(action = 'SELECT')

        bpy.ops.object.material_slot_assign()   # Assign material of the current slot to selection

        if not edit_mode:
            bpy.ops.object.mode_set(mode = 'OBJECT')

def mu_new_material_name(material):
    for mat in bpy.data.materials:
        name = mat.name

        if (name == material):
            try:
                base, suffix = name.rsplit('.', 1)

                # trigger the exception
                num = int(suffix, 10)
                material = base + "." + '%03d' % (num + 1)
            except ValueError:
                material = material + ".001"

    return material


def mu_clear_materials(object):
    #obj.data.materials.clear()

    for mat in object.material_slots:
        bpy.ops.object.material_slot_remove()


def mu_assign_material(self, material_name = "Default", override_type = 'APPEND_MATERIAL', link_override = 'KEEP'):
    """Assign the defined material to selected polygons/objects"""

    # get active object so we can restore it later
    active_object = bpy.context.active_object

    edit_mode = False
    all_polygons = True
    if (not active_object is None) and active_object.mode == 'EDIT':
        edit_mode = True
        all_polygons = False
        bpy.ops.object.mode_set()

    # check if material exists, if it doesn't then create it
    found = False
    for material in bpy.data.materials:
        if material.name == material_name:
            target = material
            found = True
            break

    if not found:
        target = bpy.data.materials.new(mu_new_material_name(material_name))
        target.use_nodes = True         # When do we not want nodes today?


    index = 0
    objects = bpy.context.selected_editable_objects

    for obj in objects:
        # Apparently selected_editable_objects includes objects as cameras etc
        if not obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
            continue

        # set the active object to our object
        scene = bpy.context.scene
        bpy.context.view_layer.objects.active = obj

        if link_override == 'KEEP':
            if len(obj.material_slots) > 0:
                link = obj.material_slots[0].link
            else:
                link = 'DATA'
        else:
            link = link_override

        # If we should override all current material slots
        if override_type == 'OVERRIDE_ALL' or obj.type == 'META':

            # If there's more than one slot, Clear out all the material slots
            if len(obj.material_slots) > 1:
                mu_clear_materials(obj)

            # If there's no slots left/never was one, add a slot
            if len(obj.material_slots) == 0:
                bpy.ops.object.material_slot_add()

            # Assign the material to that slot
            obj.material_slots[0].link = link
            obj.material_slots[0].material = target

            if obj.type == 'META':
                self.report({'INFO'}, "Meta balls only support one material, all other materials overridden!")

        # If we should override each material slot
        elif override_type == 'OVERRIDE_SLOTS':
            i = 0
            # go through each slot
            for material in obj.material_slots:
                # assign the target material to current slot
                if not link_override == 'KEEP':
                    obj.material_slots[i].link = link
                obj.material_slots[i].material = target
                i += 1

        elif override_type == 'OVERRIDE_CURRENT':
            active_slot = obj.active_material_index

            if len(obj.material_slots) == 0:
                self.report({'INFO'}, 'No material slots found! A material slot was added!')
                bpy.ops.object.material_slot_add()

            obj.material_slots[active_slot].material = target

        # if we should keep the material slots and just append the selected material (if not already assigned)
        elif override_type == 'APPEND_MATERIAL':
            found = False
            i = 0
            material_slots = obj.material_slots

            if (obj.data.users > 1) and (len(material_slots) >= 1 and material_slots[0].link == 'OBJECT'):
                self.report({'WARNING'}, 'Append material is not recommended for linked duplicates! ' +
                                            'Unwanted results might happen!')

            # check material slots for material_name materia
            for material in material_slots:
                if material.name == material_name:
                    found = True
                    index = i

                    # make slot active
                    obj.active_material_index = i
                    break
                i += 1

            if not found:
                # In Edit mode, or if there's not a slot, append the assigned material
                #  If we're overriding, there's currently no materials at all, so after this there will be 1
                #  If not, this adds another slot with the assigned material

                index = len(obj.material_slots)
                bpy.ops.object.material_slot_add()
                obj.material_slots[index].link = link
                obj.material_slots[index].material = target
                obj.active_material_index = index

            mu_assign_to_data(obj, target, index, edit_mode, all_polygons)

    # We shouldn't risk unsetting the active object
    if not active_object is None:
        # restore the active object
        bpy.context.view_layer.objects.active = active_object

    if edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def mu_select_by_material_name(self, find_material_name, extend_selection = False, internal = False):
    """Searches through all objects, or the polygons/curves of the current object
    to find and select objects/data with the desired material"""

    # in object mode selects all objects with material find_material_name
    # in edit mode selects all polygons with material find_material_name

    find_material = bpy.data.materials.get(find_material_name)

    if find_material is None:
        self.report({'INFO'}, "The material " + find_material_name + " doesn't exists!")
        return {'CANCELLED'} if not internal else -1

    # check for edit_mode
    edit_mode = False
    found_material = False

    scene = bpy.context.scene

    # set selection mode to polygons
    scene.tool_settings.mesh_select_mode = False, False, True

    active_object = bpy.context.active_object

    if (not active_object is None) and (active_object.mode == 'EDIT'):
        edit_mode = True

    if not edit_mode:
        objects = bpy.context.visible_objects

        for obj in objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                mat_slots = obj.material_slots
                for material in mat_slots:
                    if material.material == find_material:
                        obj.select_set(state = True)

                        found_material = True

                        # the active object may not have the material!
                        # set it to one that does!
                        bpy.context.view_layer.objects.active = obj
                        break
                    else:
                        if not extend_selection:
                            obj.select_set(state=False)

            #deselect non-meshes
            elif not extend_selection:
                obj.select_set(state=False)

        if not found_material:
            if not internal:
                self.report({'INFO'}, "No objects found with the material " +
                                        find_material_name + "!")
            return {'FINISHED'} if not internal else 0

    else:
        # it's edit_mode, so select the polygons

        if active_object.type == 'MESH':
            # if not extending the selection, deselect all first
            #  (Without this, edges/faces were still selected
            #   while the faces were deselected)
            if not extend_selection:
                bpy.ops.mesh.select_all(action = 'DESELECT')

        objects = bpy.context.selected_editable_objects

        for obj in objects:
            bpy.context.view_layer.objects.active = obj

            if obj.type == 'MESH':
                bpy.ops.object.mode_set()

                mat_slots = obj.material_slots

                # same material can be on multiple slots
                slot_indeces = []
                i = 0
                for material in mat_slots:
                    if material.material == find_material:
                        slot_indeces.append(i)
                    i += 1

                mesh = obj.data

                for poly in mesh.polygons:
                    if poly.material_index in slot_indeces:
                        poly.select = True
                        found_material = True
                    elif not extend_selection:
                        poly.select = False

                mesh.update()

                bpy.ops.object.mode_set(mode = 'EDIT')


            elif obj.type in {'CURVE', 'SURFACE'}:
                # For Curve objects, there can only be one material per spline
                #  and thus each spline is linked to one material slot.
                #  So to not have to care for different data structures
                #  for different curve types, we use the material slots
                #  and the built in selection methods
                #  (Technically, this should work for meshes as well)

                mat_slots = obj.material_slots

                i = 0
                for material in mat_slots:
                    bpy.context.active_object.active_material_index = i

                    if material.material == find_material:
                        bpy.ops.object.material_slot_select()
                        found_material = True
                    elif not extend_selection:
                        bpy.ops.object.material_slot_deselect()

                    i += 1

            elif not internal:
                # Some object types are not supported
                #  mostly because don't really support selecting by material (like Font/Text objects)
                #  or that they don't support multiple materials/are just "weird" (i.e. Meta balls)
                self.report({'WARNING'}, "The type '" +
                                            obj.type +
                                            "' isn't supported in Edit mode by Material Utilities!")
                #return {'CANCELLED'}

        bpy.context.view_layer.objects.active = active_object

        if (not found_material) and (not internal):
            self.report({'INFO'}, "Material " + find_material_name + " isn't assigned to anything!")

    return {'FINISHED'} if not internal else 1


def mu_copy_material_to_others(self):
    """Copy the material to of the current object to the other seleceted all_objects"""
    # Currently uses the built-in method
    #  This could be extended to work in edit mode as well

    #active_object = context.active_object

    bpy.ops.object.material_slot_copy()

    return {'FINISHED'}


def mu_cleanmatslots(self, affect):
    """Clean the material slots of the seleceted objects"""

    # check for edit mode
    edit_mode = False
    active_object = bpy.context.active_object
    if active_object.mode == 'EDIT':
        edit_mode = True
        bpy.ops.object.mode_set()

    objects = []

    if affect == 'ACTIVE':
        objects = [active_object]
    elif affect == 'SELECTED':
        objects = bpy.context.selected_editable_objects
    elif affect == 'SCENE':
        objects = bpy.context.scene.objects
    else: # affect == 'ALL'
        objects = bpy.data.objects

    for obj in objects:
        used_mat_index = []  # we'll store used materials indices here
        assigned_materials = []
        material_list = []
        material_names = []

        materials = obj.material_slots.keys()

        if obj.type == 'MESH':
            # check the polygons on the mesh to build a list of used materials
            mesh = obj.data

            for poly in mesh.polygons:
                # get the material index for this face...
                material_index = poly.material_index

                if material_index >= len(materials):
                    poly.select = True
                    self.report({'ERROR'},
                                "A poly with an invalid material was found, this should not happen! Canceling!")
                    return {'CANCELLED'}

                # indices will be lost: Store face mat use by name
                current_mat = materials[material_index]
                assigned_materials.append(current_mat)

                # check if index is already listed as used or not
                found = False
                for mat in used_mat_index:
                    if mat == material_index:
                        found = True

                if not found:
                    # add this index to the list
                    used_mat_index.append(material_index)

            # re-assign the used materials to the mesh and leave out the unused
            for u in used_mat_index:
                material_list.append(materials[u])
                # we'll need a list of names to get the face indices...
                material_names.append(materials[u])

            mu_assign_material_slots(obj, material_list)

            # restore face indices:
            i = 0
            for poly in mesh.polygons:
                material_index = material_names.index(assigned_materials[i])
                poly.material_index = material_index
                i += 1

        elif obj.type in {'CURVE', 'SURFACE'}:

            splines = obj.data.splines

            for spline in splines:
                # Get the material index of this spline
                material_index = spline.material_index

                # indices will be last: Store material use by name
                current_mat = materials[material_index]
                assigned_materials.append(current_mat)

                # check if indek is already listed as used or not
                found = False
                for mat in used_mat_index:
                    if mat == material_index:
                        found = True

                if not found:
                    # add this index to the list
                    used_mat_index.append(material_index)

            # re-assigned the used materials to the curve and leave out the unused
            for u in used_mat_index:
                material_list.append(materials[u])
                # we'll need a list of names to get the face indices
                material_names.append(materials[u])

            mu_assign_material_slots(obj, material_list)

            # restore spline indices
            i = 0
            for spline in splines:
                material_index = material_names.index(assigned_materials[i])
                spline.material_index = material_index
                i += 1

        else:
            # Some object types are not supported
            self.report({'WARNING'},
                        "The type '" + obj.type + "' isn't currently supported " +
                        "for Material slots cleaning by Material Utilities!")

    if edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}

def mu_remove_material(self, for_active_object = False):
    """Remove the active material slot from selected object(s)"""

    if for_active_object:
        bpy.ops.object.material_slot_remove()
    else:
        last_active = bpy.context.active_object
        objects = bpy.context.selected_editable_objects

        for obj in objects:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.material_slot_remove()

        bpy.context.view_layer.objects.active =  last_active

    return {'FINISHED'}

def mu_remove_all_materials(self, for_active_object = False):
    """Remove all material slots from selected object(s)"""

    if for_active_object:
        obj = bpy.context.active_object

        # Clear out the material slots
        obj.data.materials.clear()

    else:
        last_active = bpy.context.active_object
        objects = bpy.context.selected_editable_objects

        for obj in objects:
            obj.data.materials.clear()

        bpy.context.view_layer.objects.active = last_active

    return {'FINISHED'}


def mu_replace_material(material_a, material_b, all_objects=False, update_selection=False):
    """Replace one material with another material"""

    # material_a is the name of original material
    # material_b is the name of the material to replace it with
    # 'all' will replace throughout the blend file

    mat_org = bpy.data.materials.get(material_a)
    mat_rep = bpy.data.materials.get(material_b)

    if mat_org != mat_rep and None not in (mat_org, mat_rep):
        # Store active object
        scn = bpy.context.scene

        if all_objects:
            objs = bpy.data.objects
        else:
            objs = bpy.context.selected_editable_objects

        for obj in objs:
            if obj.type == 'MESH':
                match = False

                for mat in obj.material_slots:
                    if mat.material == mat_org:
                        mat.material = mat_rep

                        # Indicate which objects were affected
                        if update_selection:
                            obj.select_set(state = True)
                            match = True

                if update_selection and not match:
                    obj.select_set(state = False)

    return {'FINISHED'}


def mu_set_fake_user(self, fake_user, materials):
    """Set the fake user flag for the objects material"""

    if materials == 'ALL':
        mats = (mat for mat in bpy.data.materials if mat.library is None)
    elif materials == 'UNUSED':
        mats = (mat for mat in bpy.data.materials if mat.library is None and mat.users == 0)
    else:
        mats = []
        if materials == 'ACTIVE':
            objs = [bpy.context.active_object]
        elif materials == 'SELECTED':
            objs = bpy.context.selected_objects
        elif materials == 'SCENE':
            objs = bpy.context.scene.objects
        else: # materials == 'USED'
            objs = bpy.data.objects
            # Maybe check for users > 0 instead?

        mats = (mat for ob in objs
                    if hasattr(ob.data, "materials")
                        for mat in ob.data.materials
                            if mat.library is None)

    if fake_user == 'TOGGLE':
        done_mats = []
        for mat in mats:
            if  not mat.name in done_mats:
                mat.use_fake_user = not mat.use_fake_user
            done_mats.append(mat.name)
    else:
        fake_user_val = fake_user == 'ON'
        for mat in mats:
            mat.use_fake_user = fake_user_val

    for area in bpy.context.screen.areas:
        if area.type in ('PROPERTIES', 'NODE_EDITOR'):
            area.tag_redraw()

    return {'FINISHED'}


def mu_change_material_link(self, link, affect, override_data_material = False):
    """Change what the materials are linked to (Object or Data), while keeping materials assigned"""

    objects = []

    if affect == "ACTIVE":
        objects = [bpy.context.active_object]
    elif affect == "SELECTED":
        objects = bpy.context.selected_objects
    elif affect == "SCENE":
        objects = bpy.context.scene.objects
    elif affect == "ALL":
        objects = bpy.data.objects

    for object in objects:
        index = 0
        for slot in object.material_slots:
            present_material = slot.material

            if link == 'TOGGLE':
                slot.link = ('DATA' if slot.link == 'OBJECT' else 'OBJECT')
            else:
                slot.link = link

            if slot.link == 'OBJECT':
                override_data_material = True
            elif slot.material is None:
                override_data_material = True
            elif not override_data_material:
                self.report({'INFO'},
                            'The object Data for object ' + object.name_full + ' already had a material assigned ' +
                            'to slot #' + str(index) + ' (' + slot.material.name + '), it was not overridden!')

            if override_data_material:
                slot.material = present_material

            index = index + 1

    return {'FINISHED'}

def mu_join_objects(self, materials):
    """Join objects together based on their material"""

    for material in materials:
        mu_select_by_material_name(self, material, False, True)

        bpy.ops.object.join()

    return {'FINISHED'}

def mu_set_auto_smooth(self, angle, affect, set_smooth_shading):
    """Set Auto smooth values for selected objects"""
    # Inspired by colkai

    objects = []
    objects_affected = 0

    if affect == "ACTIVE":
        objects = [bpy.context.active_object]
    elif affect == "SELECTED":
        objects = bpy.context.selected_editable_objects
    elif affect == "SCENE":
        objects = bpy.context.scene.objects
    elif affect == "ALL":
        objects = bpy.data.objects

    if len(objects) == 0:
        self.report({'WARNING'}, 'No objects available to set Auto Smooth on')
        return {'CANCELLED'}

    for object in objects:
        if object.type == "MESH":
            if set_smooth_shading:
                for poly in object.data.polygons:
                    poly.use_smooth = True

                #bpy.ops.object.shade_smooth()

            object.data.set_sharp_from_angle(angle=angle)  # 35 degrees as radians

            objects_affected += 1

    self.report({'INFO'}, 'Auto smooth angle set to %.0f° on %d of %d objects' %
                            (degrees(angle), objects_affected, len(objects)))

    return {'FINISHED'}
