# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import os, uuid
from blenderkit import utils


def append_brush(file_name, brushname=None, link=False, fake_user=True):
    '''append a brush'''
    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        for m in data_from.brushes:
            if m == brushname or brushname is None:
                data_to.brushes = [m]
                brushname = m
    brush = bpy.data.brushes[brushname]
    if fake_user:
        brush.use_fake_user = True
    return brush


def append_material(file_name, matname=None, link=False, fake_user=True):
    '''append a material type asset'''
    # first, we have to check if there is a material with same name
    # in previous step there's check if the imported material
    # is allready in the scene, so we know same name != same material

    mats_before = bpy.data.materials.keys()

    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        for m in data_from.materials:
            if m == matname or matname is None:
                data_to.materials = [m]
                # print(m, type(m))
                matname = m
                break;

    # we have to find the new material :(
    for mname in bpy.data.materials.keys():
        if mname not in mats_before:
            mat = bpy.data.materials[mname]
            break

    if fake_user:
        mat.use_fake_user = True

    return mat


def append_scene(file_name, scenename=None, link=False, fake_user=False):
    '''append a scene type asset'''
    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        for s in data_from.scenes:
            if s == scenename or scenename is None:
                data_to.scenes = [s]
                scenename = s
    scene = bpy.data.scenes[scenename]
    if fake_user:
        scene.use_fake_user = True
    # scene has to have a new uuid, so user reports aren't screwed.
    scene['uuid'] = str(uuid.uuid4())
    return scene


def link_group(file_name, obnames=[], location=(0, 0, 0), link=False, **kwargs):
    '''link an instanced group - model type asset'''
    sel = utils.selection_get()
    bpy.ops.wm.link(directory=file_name + "/Collection/", filename=kwargs['name'], link=link, instance_collections=True,
                    autoselect=True)

    main_object = bpy.context.active_object
    if kwargs.get('rotation') is not None:
        main_object.rotation_euler = kwargs['rotation']
    main_object.location = location
    utils.selection_set(sel)
    return main_object, []


def append_particle_system(file_name, obnames=[], location=(0, 0, 0), link=False, **kwargs):
    '''link an instanced group - model type asset'''

    pss = []
    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        for ps in data_from.particles:
            pss.append(ps)
        data_to.particles = pss

    s = bpy.context.scene
    sel = utils.selection_get()

    target_object = bpy.context.scene.objects.get(kwargs['target_object'])
    if target_object is not None and target_object.type == 'MESH':
        target_object.select_set(True)
        bpy.context.view_layer.objects.active = target_object

        for ps in pss:
            # now let's tune this ps to the particular objects area:
            totarea = 0
            for p in target_object.data.polygons:
                totarea += p.area
            count = int(ps.count * totarea)
            if ps.child_type in ('INTERPOLATED', 'SIMPLE'):
                total_count = count * ps.rendered_child_count
                disp_count = count * ps.child_nbr
            else:
                total_count = count
            threshold = 2000
            total_max_threshold = 50000
            # emitting too many parent particles just kills blender now:
            if count > total_max_threshold:
                ratio = round(count / total_max_threshold)

                if ps.child_type in ('INTERPOLATED', 'SIMPLE'):
                    ps.rendered_child_count *= ratio
                else:
                    ps.child_type = 'INTERPOLATED'
                    ps.rendered_child_count = ratio
                count = max(2, int(count / ratio))
            ps.display_percentage = min(ps.display_percentage, max(1, int(100 * threshold / total_count)))

            ps.count = count
            bpy.ops.object.particle_system_add()
            target_object.particle_systems[-1].settings = ps

        target_object.select_set(False)
    utils.selection_set(sel)
    return target_object, []


def append_objects(file_name, obnames=[], location=(0, 0, 0), link=False, **kwargs):
    '''append objects into scene individually'''
    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        sobs = []
        for ob in data_from.objects:
            if ob in obnames or obnames == []:
                sobs.append(ob)
        data_to.objects = sobs
        # data_to.objects = data_from.objects#[name for name in data_from.objects if name.startswith("house")]

    # link them to scene
    scene = bpy.context.scene
    sel = utils.selection_get()
    bpy.ops.object.select_all(action='DESELECT')

    return_obs = []  # this might not be needed, but better be sure to rewrite the list.
    main_object = None
    hidden_objects = []
    #
    for obj in data_to.objects:
        if obj is not None:
            # if obj.name not in scene.objects:
            scene.collection.objects.link(obj)
            if obj.parent is None:
                obj.location = location
                main_object = obj
            obj.select_set(True)
            # we need to unhide object so make_local op can use those too.
            if link == True:
                if obj.hide_viewport:
                    hidden_objects.append(obj)
                    obj.hide_viewport = False
            return_obs.append(obj)

    # Only after all objects are in scene! Otherwise gets broken relationships
    if link == True:
        bpy.ops.object.make_local(type='SELECT_OBJECT')
        for ob in hidden_objects:
            ob.hide_viewport = True

    if kwargs.get('rotation') is not None:
        main_object.rotation_euler = kwargs['rotation']
    bpy.ops.object.select_all(action='DESELECT')

    utils.selection_set(sel)
    return main_object, return_obs
