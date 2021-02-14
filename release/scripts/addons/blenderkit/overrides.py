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


from blenderkit import utils

import bpy, mathutils
from bpy.types import (
    Operator)


def getNodes(nt, node_type='OUTPUT_MATERIAL'):
    chnodes = nt.nodes[:]
    nodes = []
    while len(chnodes) > 0:
        n = chnodes.pop()
        if n.type == node_type:
            nodes.append(n)
        if n.type == 'GROUP':
            chnodes.extend(n.node_tree.nodes)
    return nodes


def getShadersCrawl(nt, chnodes):
    shaders = []
    done_nodes = chnodes[:]

    while len(chnodes) > 0:
        check_node = chnodes.pop()
        is_shader = False
        for o in check_node.outputs:
            if o.type == 'SHADER':
                is_shader = True
        for i in check_node.inputs:
            if i.type == 'SHADER':
                is_shader = False  # this is for mix nodes and group inputs..
                if len(i.links) > 0:
                    for l in i.links:
                        fn = l.from_node
                        if fn not in done_nodes:
                            done_nodes.append(fn)
                            chnodes.append(fn)
                            if fn.type == 'GROUP':
                                group_outputs = getNodes(fn.node_tree, node_type='GROUP_OUTPUT')
                                shaders.extend(getShadersCrawl(fn.node_tree, group_outputs))

        if check_node.type == 'GROUP':
            is_shader = False

        if is_shader:
            shaders.append((check_node, nt))

    return (shaders)


def addColorCorrectors(material):
    nt = material.node_tree
    output = getNodes(nt, 'OUTPUT_MATERIAL')[0]
    shaders = getShadersCrawl(nt, [output])

    correctors = []
    for shader, nt in shaders:

        if shader.type != 'BSDF_TRANSPARENT':  # exclude transparent for color tweaks
            for i in shader.inputs:
                if i.type == 'RGBA':
                    if len(i.links) > 0:
                        l = i.links[0]
                        if not (l.from_node.type == 'GROUP' and l.from_node.node_tree.name == 'bkit_asset_tweaker'):
                            from_socket = l.from_socket
                            to_socket = l.to_socket

                            g = nt.nodes.new(type='ShaderNodeGroup')
                            g.node_tree = bpy.data.node_groups['bkit_asset_tweaker']
                            g.location = shader.location
                            g.location.x -= 100

                            nt.links.new(from_socket, g.inputs[0])
                            nt.links.new(g.outputs[0], to_socket)
                        else:
                            g = l.from_node
                        tweakers.append(g)
                    else:
                        g = nt.nodes.new(type='ShaderNodeGroup')
                        g.node_tree = bpy.data.node_groups['bkit_asset_tweaker']
                        g.location = shader.location
                        g.location.x -= 100

                        nt.links.new(g.outputs[0], i)
                        correctors.append(g)


def modelProxy():
    s = bpy.context.scene
    ao = bpy.context.active_object
    if utils.is_linked_asset(ao):
        utils.activate(ao)

        g = ao.instance_collection

        rigs = []

        for ob in g.objects:
            if ob.type == 'ARMATURE':
                rigs.append(ob)

        if len(rigs) == 1:

            ao.instance_collection = None
            bpy.ops.object.duplicate()
            new_ao = bpy.context.view_layer.objects.active
            new_ao.instance_collection = g
            new_ao.empty_display_type = 'SPHERE'
            new_ao.empty_display_size *= 0.1

            bpy.ops.object.proxy_make(object=rigs[0].name)
            proxy = bpy.context.active_object
            bpy.context.view_layer.objects.active = ao
            ao.select_set(True)
            new_ao.select_set(True)
            new_ao.use_extra_recalc_object = True
            new_ao.use_extra_recalc_data = True
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            return True
        else:  # TODO report this to ui
            utils.p('not sure what to proxify')
    return False


eevee_transp_nodes = [
    'BSDF_GLASS',
    'BSDF_REFRACTION',
    'BSDF_TRANSPARENT',
    'PRINCIPLED_VOLUME',
    'VOLUME_ABSORPTION',
    'VOLUME_SCATTER'
]


def ensure_eevee_transparency(m):
    ''' ensures alpha for transparent materials when the user didn't set it up correctly'''
    # if the blend mode is opaque, it means user probably ddidn't know or forgot to
    # set up material properly
    if m.blend_method == 'OPAQUE':
        alpha = False
        for n in m.node_tree.nodes:
            if n.type in eevee_transp_nodes:
                alpha = True
            elif n.type == 'BSDF_PRINCIPLED':
                i = n.inputs['Transmission']
                if i.default_value > 0 or len(i.links) > 0:
                    alpha = True
        if alpha:
            m.blend_method = 'HASHED'
            m.shadow_method = 'HASHED'


class BringToScene(Operator):
    """Bring linked object hierarchy to scene and make it editable"""

    bl_idname = "object.blenderkit_bring_to_scene"
    bl_label = "BlenderKit bring objects to scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bpy.context.view_layer.objects.active is not None

    def execute(self, context):

        s = bpy.context.scene
        sobs = s.collection.all_objects
        aob = bpy.context.active_object
        dg = aob.instance_collection
        vlayer = bpy.context.view_layer
        instances_emptys = []

        # first, find instances of this collection in the scene
        for ob in sobs:
            if ob.instance_collection == dg and ob not in instances_emptys:
                instances_emptys.append(ob)
                ob.instance_collection = None
                ob.instance_type = 'NONE'
        # dg.make_local
        parent = None
        obs = []
        for ob in dg.objects:
            dg.objects.unlink(ob)
            try:
                s.collection.objects.link(ob)
                ob.select_set(True)
                obs.append(ob)
                if ob.parent == None:
                    parent = ob
                    bpy.context.view_layer.objects.active = parent
            except Exception as e:
                print(e)

        bpy.ops.object.make_local(type='ALL')

        for i, ob in enumerate(obs):
            if ob.name in vlayer.objects:
                obs[i] = vlayer.objects[ob.name]
                try:
                    ob.select_set(True)
                except Exception as e:
                    print('failed to select an object from the collection, getting a replacement.')
                    print(e)

        related = []

        for i, ob in enumerate(instances_emptys):
            if i > 0:
                bpy.ops.object.duplicate(linked=True)

            related.append([ob, bpy.context.active_object, mathutils.Vector(bpy.context.active_object.scale)])

        for relation in related:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = relation[0]
            relation[0].select_set(True)
            relation[1].select_set(True)
            relation[1].matrix_world = relation[0].matrix_world
            relation[1].scale.x = relation[2].x * relation[0].scale.x
            relation[1].scale.y = relation[2].y * relation[0].scale.y
            relation[1].scale.z = relation[2].z * relation[0].scale.z
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        return {'FINISHED'}


class ModelProxy(Operator):
    """Attempt to create proxy armature from the asset"""
    bl_idname = "object.blenderkit_make_proxy"
    bl_label = "BlenderKit Make Proxy"

    @classmethod
    def poll(cls, context):
        return bpy.context.view_layer.objects.active is not None

    def execute(self, context):
        result = modelProxy()
        if not result:
            self.report({'INFO'}, 'No proxy made.There is no armature or more than one in the model.')
        return {'FINISHED'}


class ColorCorrector(Operator):
    """Add color corector to the asset. """
    bl_idname = "object.blenderkit_color_corrector"
    bl_label = "Add color corrector"

    @classmethod
    def poll(cls, context):
        return bpy.context.view_layer.objects.active is not None

    def execute(self, context):
        ao = bpy.context.active_object
        g = ao.instance_collection
        ao['color correctors'] = []
        mats = []

        for o in g.objects:
            for ms in o.material_slots:
                if ms.material not in mats:
                    mats.append(ms.material)
        for mat in mats:
            correctors = addColorCorrectors(mat)

        return 'FINISHED'


def register_overrides():
    bpy.utils.register_class(BringToScene)
    bpy.utils.register_class(ModelProxy)
    bpy.utils.register_class(ColorCorrector)


def unregister_overrides():
    bpy.utils.unregister_class(BringToScene)
    bpy.utils.unregister_class(ModelProxy)
    bpy.utils.unregister_class(ColorCorrector)
