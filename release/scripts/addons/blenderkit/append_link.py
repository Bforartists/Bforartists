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


from blenderkit import utils, ui

import bpy
import uuid


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
    # is already in the scene, so we know same name != same material

    mats_before = bpy.data.materials[:]
    try:
        with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
            found = False
            for m in data_from.materials:
                if m == matname or matname is None:
                    data_to.materials = [m]
                    # print(m, type(m))
                    matname = m
                    found = True
                    break;

            #not found yet? probably some name inconsistency then.
            if not found and len(data_from.materials)>0:
                data_to.materials = [data_from.materials[0]]
                matname = data_from.materials[0]
                print(f"the material wasn't found under the exact name, appended another one: {matname}")
            # print('in the appended file the name is ', matname)

    except Exception as e:
        print(e)
        print('failed to open the asset file')
    # we have to find the new material , due to possible name changes
    mat = None
    for m in bpy.data.materials:
        if m not in mats_before:
            mat = m
            break;
    #still not found?
    if mat is None:
        mat = bpy.data.materials.get(matname)

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

    #reset ui_props of the scene to defaults:
    ui_props = bpy.context.scene.blenderkitUI
    ui_props.down_up = 'SEARCH'

    return scene


def get_node_sure(node_tree, ntype=''):
    '''
    Gets a node of certain type, but creates a new one if not pre
    '''
    node = None
    for n in node_tree.nodes:
        if ntype == n.bl_rna.identifier:
            node = n
            return node
    if not node:
        node = node_tree.nodes.new(type=ntype)

    return node

def hdr_swap(name, hdr):
    '''
    Try to replace the hdr in current world setup. If this fails, create a new world.
    :param name: Name of the resulting world (renamse the current one if swap is successfull)
    :param hdr: Image type
    :return: None
    '''
    w = bpy.context.scene.world
    if w:
        w.use_nodes = True
        w.name = name
        nt = w.node_tree
        for n in nt.nodes:
            if 'ShaderNodeTexEnvironment' == n.bl_rna.identifier:
                env_node = n
                env_node.image = hdr
                return
    new_hdr_world(name,hdr)


def new_hdr_world(name, hdr):
    '''
    creates a new world, links in the hdr with mapping node, and links the world to scene
    :param name: Name of the world datablock
    :param hdr: Image type
    :return: None
    '''
    w = bpy.data.worlds.new(name=name)
    w.use_nodes = True
    bpy.context.scene.world = w

    nt = w.node_tree
    env_node = nt.nodes.new(type='ShaderNodeTexEnvironment')
    env_node.image = hdr
    background = get_node_sure(nt, 'ShaderNodeBackground')
    tex_coord = get_node_sure(nt, 'ShaderNodeTexCoord')
    mapping = get_node_sure(nt, 'ShaderNodeMapping')

    nt.links.new(env_node.outputs['Color'], background.inputs['Color'])
    nt.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], env_node.inputs['Vector'])
    env_node.location.x = -400
    mapping.location.x = -600
    tex_coord.location.x = -800


def load_HDR(file_name, name):
    '''Load a HDR into file and link it to scene world. '''
    already_linked = False
    for i in bpy.data.images:
        if i.filepath == file_name:
            hdr = i
            already_linked = True
            break;

    if not already_linked:
        hdr = bpy.data.images.load(file_name)

    hdr_swap(name, hdr)
    return hdr


def link_collection(file_name, obnames=[], location=(0, 0, 0), link=False, parent = None, **kwargs):
    '''link an instanced group - model type asset'''
    sel = utils.selection_get()

    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        scols = []
        for col in data_from.collections:
            if col == kwargs['name']:
                data_to.collections = [col]

    rotation = (0, 0, 0)
    if kwargs.get('rotation') is not None:
        rotation = kwargs['rotation']

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location, rotation=rotation)
    main_object = bpy.context.view_layer.objects.active
    main_object.instance_type = 'COLLECTION'

    if parent is not None:
        main_object.parent = bpy.data.objects.get(parent)

    main_object.matrix_world.translation = location

    for col in bpy.data.collections:
        if col.library is not None:
            fp = bpy.path.abspath(col.library.filepath)
            fp1 = bpy.path.abspath(file_name)
            if fp == fp1:
                main_object.instance_collection = col
                break;

    #sometimes, the lib might already  be without the actual link.
    if not main_object.instance_collection and kwargs['name']:
        col = bpy.data.collections.get(kwargs['name'])
        if col:
            main_object.instance_collection = col

    main_object.name = main_object.instance_collection.name

    # bpy.ops.wm.link(directory=file_name + "/Collection/", filename=kwargs['name'], link=link, instance_collections=True,
    #                 autoselect=True)
    # main_object = bpy.context.view_layer.objects.active
    # if kwargs.get('rotation') is not None:
    #     main_object.rotation_euler = kwargs['rotation']
    # main_object.location = location

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

            bbox_threshold = 25000
            display_threshold = 200000
            total_max_threshold = 2000000
            # emitting too many parent particles just kills blender now.

            #this part tuned child count, we'll leave children to artists only.
            # if count > total_max_threshold:
            #     ratio = round(count / total_max_threshold)
            #
            #     if ps.child_type in ('INTERPOLATED', 'SIMPLE'):
            #         ps.rendered_child_count *= ratio
            #     else:
            #         ps.child_type = 'INTERPOLATED'
            #         ps.rendered_child_count = ratio
            #     count = max(2, int(count / ratio))

            #1st level of optimizaton - switch t bounding boxes.
            if total_count>bbox_threshold:
                target_object.display_type = 'BOUNDS'
            # 2nd level of optimization - reduce percentage of displayed particles.
            ps.display_percentage = min(ps.display_percentage, max(1, int(100 * display_threshold / total_count)))
            #here we can also tune down number of children displayed.
            #set the count
            ps.count = count
            #add the modifier
            bpy.ops.object.particle_system_add()
            # 3rd level - hide particle system from viewport - is done on the modifier..
            if total_count > total_max_threshold:
                target_object.modifiers[-1].show_viewport = False

            target_object.particle_systems[-1].settings = ps

        target_object.select_set(False)
    utils.selection_set(sel)
    return target_object, []


def append_objects(file_name, obnames=[], location=(0, 0, 0), link=False, **kwargs):
    '''append objects into scene individually'''
    #simplified version of append
    if kwargs.get('name'):
        # by now used for appending into scene
        scene = bpy.context.scene
        sel = utils.selection_get()
        bpy.ops.object.select_all(action='DESELECT')

        path = file_name + "\\Collection\\"
        object_name = kwargs.get('name')
        fc = utils.get_fake_context(bpy.context, area_type='VIEW_3D')
        bpy.ops.wm.append(fc, filename=object_name, directory=path)

        return_obs = []
        for ob in bpy.context.scene.objects:
            if ob.select_get():
                return_obs.append(ob)
                if not ob.parent:
                    main_object = ob
                    ob.location = location

        if kwargs.get('rotation'):
            main_object.rotation_euler = kwargs['rotation']

        if kwargs.get('parent') is not None:
            main_object.parent = bpy.data.objects[kwargs['parent']]
            main_object.matrix_world.translation = location

        bpy.ops.object.select_all(action='DESELECT')
        utils.selection_set(sel)

        return main_object, return_obs
    #this is used for uploads:
    with bpy.data.libraries.load(file_name, link=link, relative=True) as (data_from, data_to):
        sobs = []
        # for col in data_from.collections:
        #     if col == kwargs.get('name'):
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

    if kwargs.get('parent') is not None:
        main_object.parent = bpy.data.objects[kwargs['parent']]
        main_object.matrix_world.translation = location

    bpy.ops.object.select_all(action='DESELECT')

    utils.selection_set(sel)


    return main_object, return_obs
