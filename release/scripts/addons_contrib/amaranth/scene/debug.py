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
"""
Scene Debug Panel

This is something I've been wanting to have for a while, a way to know
certain info about your scene. A way to "debug" it, especially when
working in production with other teams, this came in very handy.

Being mostly a lighting guy myself, I needed two main features to start with:

* List Cycles Material using X shader
Where X is any shader type you want. It will display (and print on console)
a list of all the materials containing the shader you specified above.
Good for finding out if there's any Meshlight (Emission) material hidden,
or if there are many glossy shaders making things noisy.
A current limitation is that it doesn't look inside node groups (yet,
working on it!). It works since 0.8.8!

* Lamps List
This is a collapsable list of Lamps in the scene(s).
It allows you to quickly see how many lamps you have, select them by
clicking on their name, see their type (icon), samples number (if using
Branched Path Tracing), size, and change their visibility.
The active lamp is indicated by a triangle on the right.

Under the "Scene Debug" panel in Scene properties.
"""

# TODO: module cleanup! maybe break it up in a package
#     dicts instead of if, elif,else all over the place.
#     helper functions instead of everything on the execute method.
#     str.format() + dicts instead of inline % op all over the place.
#     remove/manage debug print calls.
#     self.__class__.attr? use type(self).attr or self.attr instead.
#     avoid duplicate code/patterns through helper functions.

import os
import bpy
from amaranth import utils


def init():
    scene = bpy.types.Scene

    scene.amaranth_debug_scene_list_missing_images = bpy.props.BoolProperty(
        default=False,
        name="List Missing Images",
        description="Display a list of all the missing images")

    scene.amaranth_lighterscorner_list_meshlights = bpy.props.BoolProperty(
        default=False,
        name="List Meshlights",
        description="Include light emitting meshes on the list")

    amth_datablock_types = (
        ("IMAGE_DATA", "Image", "Image Datablocks", 0),
        ("MATERIAL", "Material", "Material Datablocks", 1),
        ("GROUP_VCOL", "Vertex Colors", "Vertex Color Layers", 2),
    )
    scene.amth_datablock_types = bpy.props.EnumProperty(
        items=amth_datablock_types,
        name="Type",
        description="Datablock Type")

    if utils.cycles_exists():
        cycles_shader_node_types = (
            ("BSDF_DIFFUSE", "Diffuse BSDF", "", 0),
            ("BSDF_GLOSSY", "Glossy BSDF", "", 1),
            ("BSDF_TRANSPARENT", "Transparent BSDF", "", 2),
            ("BSDF_REFRACTION", "Refraction BSDF", "", 3),
            ("BSDF_GLASS", "Glass BSDF", "", 4),
            ("BSDF_TRANSLUCENT", "Translucent BSDF", "", 5),
            ("BSDF_ANISOTROPIC", "Anisotropic BSDF", "", 6),
            ("BSDF_VELVET", "Velvet BSDF", "", 7),
            ("BSDF_TOON", "Toon BSDF", "", 8),
            ("SUBSURFACE_SCATTERING", "Subsurface Scattering", "", 9),
            ("EMISSION", "Emission", "", 10),
            ("BSDF_HAIR", "Hair BSDF", "", 11),
            ("BACKGROUND", "Background", "", 12),
            ("AMBIENT_OCCLUSION", "Ambient Occlusion", "", 13),
            ("HOLDOUT", "Holdout", "", 14),
            ("VOLUME_ABSORPTION", "Volume Absorption", "", 15),
            ("VOLUME_SCATTER", "Volume Scatter", "", 16),
            ("MIX_SHADER", "Mix Shader", "", 17),
            ("ADD_SHADER", "Add Shader", "", 18),
        )
        scene.amaranth_cycles_node_types = bpy.props.EnumProperty(
            items=cycles_shader_node_types, name="Shader")


def clear():
    props = (
        "amaranth_debug_scene_list_missing_images",
        "amaranth_cycles_node_types",
        "amaranth_lighterscorner_list_meshlights",
    )
    wm = bpy.context.window_manager
    for p in props:
        if wm.get(p):
            del wm[p]


class AMTH_SCENE_OT_cycles_shader_list_nodes(bpy.types.Operator):

    """List Cycles materials containing a specific shader"""
    bl_idname = "scene.cycles_list_nodes"
    bl_label = "List Materials"
    materials = []

    @classmethod
    def poll(cls, context):
        return utils.cycles_exists() and utils.cycles_active(context)

    def execute(self, context):
        node_type = context.scene.amaranth_cycles_node_types
        roughness = False
        self.__class__.materials = []
        shaders_roughness = ("BSDF_GLOSSY", "BSDF_DIFFUSE", "BSDF_GLASS")

        print("\n=== Cycles Shader Type: %s === \n" % node_type)

        for ma in bpy.data.materials:
            if ma.node_tree:
                nodes = ma.node_tree.nodes

                print_unconnected = (
                    "Note: \nOutput from \"%s\" node" % node_type,
                    "in material \"%s\"" % ma.name, "not connected\n")

                for no in nodes:
                    if no.type == node_type:
                        for ou in no.outputs:
                            if ou.links:
                                connected = True
                                if no.type in shaders_roughness:
                                    roughness = "R: %.4f" % no.inputs[
                                        "Roughness"].default_value
                                else:
                                    roughness = False
                            else:
                                connected = False
                                print(print_unconnected)

                            if ma.name not in self.__class__.materials:
                                self.__class__.materials.append(
                                    "%s%s [%s] %s%s%s" %
                                    ("[L] " if ma.library else "",
                                     ma.name,
                                     ma.users,
                                     "[F]" if ma.use_fake_user else "",
                                     " - [%s]" %
                                     roughness if roughness else "",
                                     " * Output not connected" if not connected else ""))

                    elif no.type == "GROUP":
                        if no.node_tree:
                            for nog in no.node_tree.nodes:
                                if nog.type == node_type:
                                    for ou in nog.outputs:
                                        if ou.links:
                                            connected = True
                                            if nog.type in shaders_roughness:
                                                roughness = "R: %.4f" % nog.inputs[
                                                    "Roughness"].default_value
                                            else:
                                                roughness = False
                                        else:
                                            connected = False
                                            print(print_unconnected)

                                        if ma.name not in self.__class__.materials:
                                            self.__class__.materials.append(
                                                '%s%s%s [%s] %s%s%s' %
                                                ("[L] " if ma.library else "",
                                                 "Node Group:  %s%s  ->  " %
                                                 ("[L] " if no.node_tree.library else "",
                                                  no.node_tree.name),
                                                    ma.name,
                                                    ma.users,
                                                    "[F]" if ma.use_fake_user else "",
                                                    " - [%s]" %
                                                    roughness if roughness else "",
                                                    " * Output not connected" if not connected else ""))

                    self.__class__.materials = sorted(
                        list(set(self.__class__.materials)))

        if len(self.__class__.materials) == 0:
            self.report({"INFO"},
                        "No materials with nodes type %s found" % node_type)
        else:
            print("* A total of %d %s using %s was found \n" % (
                len(self.__class__.materials),
                "material" if len(
                    self.__class__.materials) == 1 else "materials",
                node_type))

            count = 0

            for mat in self.__class__.materials:
                print('%02d. %s' %
                      (count + 1, self.__class__.materials[count]))
                count += 1
            print("\n")

        self.__class__.materials = sorted(list(set(self.__class__.materials)))

        return {"FINISHED"}


class AMTH_SCENE_OT_cycles_shader_list_nodes_clear(bpy.types.Operator):

    """Clear the list below"""
    bl_idname = "scene.cycles_list_nodes_clear"
    bl_label = "Clear Materials List"

    @classmethod
    def poll(cls, context):
        return utils.cycles_exists()

    def execute(self, context):
        AMTH_SCENE_OT_cycles_shader_list_nodes.materials[:] = []
        print("* Cleared Cycles Materials List")
        return {"FINISHED"}


class AMTH_SCENE_OT_amaranth_object_select(bpy.types.Operator):

    """Select object"""
    bl_idname = "scene.amaranth_object_select"
    bl_label = "Select Object"
    object = bpy.props.StringProperty()

    def execute(self, context):
        if self.object:
            object = bpy.data.objects[self.object]

            bpy.ops.object.select_all(action="DESELECT")
            object.select = True
            context.scene.objects.active = object

        return {"FINISHED"}


class AMTH_SCENE_OT_list_missing_node_links(bpy.types.Operator):

    """Print a list of missing node links"""
    bl_idname = "scene.list_missing_node_links"
    bl_label = "List Missing Node Links"

    count_groups = 0
    count_images = 0
    count_image_node_unlinked = 0

    def execute(self, context):
        missing_groups = []
        missing_images = []
        image_nodes_unlinked = []
        libraries = []
        self.__class__.count_groups = 0
        self.__class__.count_images = 0
        self.__class__.count_image_node_unlinked = 0

        for ma in bpy.data.materials:
            if ma.node_tree:
                for no in ma.node_tree.nodes:
                    if no.type == "GROUP":
                        if not no.node_tree:
                            self.__class__.count_groups += 1

                            users_ngroup = []

                            for ob in bpy.data.objects:
                                if ob.material_slots and ma.name in ob.material_slots:
                                    users_ngroup.append("%s%s%s" % (
                                        "[L] " if ob.library else "",
                                        "[F] " if ob.use_fake_user else "",
                                        ob.name))

                            missing_groups.append(
                                "MA: %s%s%s [%s]%s%s%s\n" %
                                ("[L] " if ma.library else "",
                                 "[F] " if ma.use_fake_user else "",
                                 ma.name,
                                 ma.users,
                                 " *** No users *** " if ma.users == 0 else "",
                                 "\nLI: %s" %
                                 ma.library.filepath if ma.library else "",
                                 "\nOB: %s" %
                                 ",  ".join(users_ngroup) if users_ngroup else ""))

                            if ma.library:
                                libraries.append(ma.library.filepath)
                    if no.type == "TEX_IMAGE":

                        outputs_empty = not no.outputs[
                            "Color"].is_linked and not no.outputs["Alpha"].is_linked

                        if no.image:
                            image_path_exists = os.path.exists(
                                bpy.path.abspath(
                                    no.image.filepath,
                                    library=no.image.library))

                        if outputs_empty or not \
                           no.image or not \
                           image_path_exists:

                            users_images = []

                            for ob in bpy.data.objects:
                                if ob.material_slots and ma.name in ob.material_slots:
                                    users_images.append("%s%s%s" % (
                                        "[L] " if ob.library else "",
                                        "[F] " if ob.use_fake_user else "",
                                        ob.name))

                            if outputs_empty:
                                self.__class__.count_image_node_unlinked += 1

                                image_nodes_unlinked.append(
                                    "%s%s%s%s%s [%s]%s%s%s%s%s\n" %
                                    ("NO: %s" %
                                     no.name,
                                     "\nMA: ",
                                     "[L] " if ma.library else "",
                                     "[F] " if ma.use_fake_user else "",
                                     ma.name,
                                     ma.users,
                                     " *** No users *** " if ma.users == 0 else "",
                                     "\nLI: %s" %
                                     ma.library.filepath if ma.library else "",
                                     "\nIM: %s" %
                                     no.image.name if no.image else "",
                                     "\nLI: %s" %
                                     no.image.filepath if no.image and no.image.filepath else "",
                                     "\nOB: %s" %
                                     ',  '.join(users_images) if users_images else ""))

                            if not no.image or not image_path_exists:
                                self.__class__.count_images += 1

                                missing_images.append(
                                    "MA: %s%s%s [%s]%s%s%s%s%s\n" %
                                    ("[L] " if ma.library else "",
                                     "[F] " if ma.use_fake_user else "",
                                     ma.name,
                                     ma.users,
                                     " *** No users *** " if ma.users == 0 else "",
                                     "\nLI: %s" %
                                     ma.library.filepath if ma.library else "",
                                     "\nIM: %s" %
                                     no.image.name if no.image else "",
                                     "\nLI: %s" %
                                     no.image.filepath if no.image and no.image.filepath else "",
                                     "\nOB: %s" %
                                     ',  '.join(users_images) if users_images else ""))

                                if ma.library:
                                    libraries.append(ma.library.filepath)

        # Remove duplicates and sort
        missing_groups = sorted(list(set(missing_groups)))
        missing_images = sorted(list(set(missing_images)))
        image_nodes_unlinked = sorted(list(set(image_nodes_unlinked)))
        libraries = sorted(list(set(libraries)))

        print(
            "\n\n== %s missing image %s, %s missing node %s and %s image %s unlinked ==" %
            ("No" if self.__class__.count_images == 0 else str(
                self.__class__.count_images),
                "node" if self.__class__.count_images == 1 else "nodes",
                "no" if self.__class__.count_groups == 0 else str(
                    self.__class__.count_groups),
                "group" if self.__class__.count_groups == 1 else "groups",
                "no" if self.__class__.count_image_node_unlinked == 0 else str(
                    self.__class__.count_image_node_unlinked),
                "node" if self.__class__.count_groups == 1 else "nodes"))

        # List Missing Node Groups
        if missing_groups:
            print("\n* Missing Node Group Links\n")
            for mig in missing_groups:
                print(mig)

        # List Missing Image Nodes
        if missing_images:
            print("\n* Missing Image Nodes Link\n")

            for mii in missing_images:
                print(mii)

        # List Image Nodes with its outputs unlinked
        if image_nodes_unlinked:
            print("\n* Image Nodes Unlinked\n")

            for nou in image_nodes_unlinked:
                print(nou)

        if missing_groups or \
           missing_images or \
           image_nodes_unlinked:
            if libraries:
                print(
                    "\nThat's bad, run check on %s:" %
                    ("this library" if len(libraries) == 1 else "these libraries"))
                for li in libraries:
                    print(li)
        else:
            self.report({"INFO"}, "Yay! No missing node links")

        print("\n")

        if missing_groups and missing_images:
            self.report(
                {"WARNING"},
                "%d missing image %s and %d missing node %s found" %
                (self.__class__.count_images,
                 "node" if self.__class__.count_images == 1 else "nodes",
                 self.__class__.count_groups,
                 "group" if self.__class__.count_groups == 1 else "groups"))

        return {"FINISHED"}


class AMTH_SCENE_OT_list_missing_material_slots(bpy.types.Operator):

    """List objects with empty material slots"""
    bl_idname = "scene.list_missing_material_slots"
    bl_label = "List Empty Material Slots"

    objects = []
    libraries = []

    def execute(self, context):
        self.__class__.objects = []
        self.__class__.libraries = []

        for ob in bpy.data.objects:
            for ma in ob.material_slots:
                if not ma.material:
                    self.__class__.objects.append('%s%s' % (
                        '[L] ' if ob.library else '',
                        ob.name))
                    if ob.library:
                        self.__class__.libraries.append(ob.library.filepath)

        self.__class__.objects = sorted(list(set(self.__class__.objects)))
        self.__class__.libraries = sorted(list(set(self.__class__.libraries)))

        if len(self.__class__.objects) == 0:
            self.report({"INFO"},
                        "No objects with empty material slots found")
        else:
            print(
                "\n* A total of %d %s with empty material slots was found \n" %
                (len(
                    self.__class__.objects), "object" if len(
                    self.__class__.objects) == 1 else "objects"))

            count = 0
            count_lib = 0

            for obs in self.__class__.objects:
                print('%02d. %s' % (
                    count + 1, self.__class__.objects[count]))
                count += 1

            if self.__class__.libraries:
                print("\n\n* Check %s:\n" %
                     ("this library" if len(self.__class__.libraries) == 1
                      else "these libraries"))

                for libs in self.__class__.libraries:
                    print('%02d. %s' % (
                        count_lib + 1, self.__class__.libraries[count_lib]))
                    count_lib += 1
            print("\n")

        return {"FINISHED"}


class AMTH_SCENE_OT_list_missing_material_slots_clear(bpy.types.Operator):

    """Clear the list below"""
    bl_idname = "scene.list_missing_material_slots_clear"
    bl_label = "Clear Empty Material Slots List"

    def execute(self, context):
        AMTH_SCENE_OT_list_missing_material_slots.objects[:] = []
        print("* Cleared Empty Material Slots List")
        return {"FINISHED"}


class AMTH_SCENE_OT_list_users_for_x_type(bpy.types.Operator):
    bl_idname = "scene.amth_list_users_for_x_type"
    bl_label = "Select"
    bl_description = "Select Datablock Name"

    def avail(self,context):
        datablock_type = bpy.context.scene.amth_datablock_types

        if datablock_type == 'IMAGE_DATA':
            where = []
            for im in bpy.data.images:
                if im.name not in {'Render Result', 'Viewer Node'}:
                    where.append(im)

        elif datablock_type == 'MATERIAL':
            where = bpy.data.materials

        elif datablock_type == 'GROUP_VCOL':
            where = []
            for ob in bpy.data.objects:
                if ob.type == 'MESH':
                    for v in ob.data.vertex_colors:
                        if v and v not in where:
                            where.append(v)
            where = list(set(where))

        items = [(str(i),x.name,x.name, datablock_type, i) for i,x in enumerate(where)]
        items = sorted(list(set(items)))
        return items

    list_type_select = bpy.props.EnumProperty(items = avail, name = "Available")

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.amth_datablock_types

    def execute(self,context):
        datablock_type = bpy.context.scene.amth_datablock_types

        if datablock_type == 'IMAGE_DATA':
            where = []
            for im in bpy.data.images:
                if im.name not in {'Render Result', 'Viewer Node'}:
                    where.append(im)

        elif datablock_type == 'MATERIAL':
            where = bpy.data.materials

        elif datablock_type == 'GROUP_VCOL':
            where = []
            for ob in bpy.data.objects:
                if ob.type == 'MESH':
                    for v in ob.data.vertex_colors:
                        if v and v not in where:
                            where.append(v)
            where = list(set(where))

        bpy.context.scene.amth_list_users_for_x_name = where[int(self.list_type_select)].name
        return {'FINISHED'}


class AMTH_SCENE_OT_list_users_for_x(bpy.types.Operator):

    """List users for a particular datablock"""
    bl_idname = "scene.amth_list_users_for_x"
    bl_label = "List Users for Datablock"

    name = bpy.props.StringProperty()
    users = {}
    libraries = []

    def execute(self, context):

        datablock_type = context.scene.amth_datablock_types
        d = bpy.data

        if self.name:
            x = self.name
        else:
            x = context.scene.amth_list_users_for_x_name

        dtype = context.scene.amth_datablock_types

        self.__class__.users = {
            'OBJECT_DATA' : [], # Store Objects with Material
            'MATERIAL' : [], # Materials (Node tree)
            'LAMP' : [], # Lamps
            'WORLD' : [], # World
            'TEXTURE' : [], # Textures (Psys, Brushes)
            'MODIFIER' : [], # Modifiers
            'MESH_DATA' : [], # Vertex Colors
            'VIEW3D' : [], # Background Images
            'NODETREE' : [], # Compositor
        }

        # IMAGE TYPE
        if dtype == 'IMAGE_DATA':
            # Check Materials
            for ma in d.materials:
                # Cycles
                if utils.cycles_exists():
                    if ma and ma.node_tree and ma.node_tree.nodes:
                        materials = []

                        for nd in ma.node_tree.nodes:
                            if nd and nd.type in {'TEX_IMAGE','TEX_ENVIRONMENT'}:
                                materials.append(nd)
                            if nd and nd.type == 'GROUP':
                                if nd.node_tree and nd.node_tree.nodes:
                                    for ng in nd.node_tree.nodes:
                                        if ng.type in {'TEX_IMAGE','TEX_ENVIRONMENT'}:
                                            materials.append(ng)

                            for no in materials:
                                if no.image and no.image.name == x:
                                    objects = []

                                    for ob in d.objects:
                                        if ma.name in ob.material_slots:
                                            objects.append(ob.name)

                                    links = False

                                    for o in no.outputs:
                                        if o.links:
                                            links = True

                                    name = '"{0}" {1}{2}'.format(
                                            ma.name,
                                            'in object: {0}'.format(objects) if objects else ' (unassigned)',
                                            '' if links else ' (unconnected)')

                                    if name not in self.__class__.users['MATERIAL']:
                                        self.__class__.users['MATERIAL'].append(name)

            # Check Lamps
            for la in d.lamps:
                # Cycles
                if utils.cycles_exists():
                    if la and la.node_tree and la.node_tree.nodes:
                        for no in la.node_tree.nodes:
                            if no and \
                               no.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} and \
                               no.image and no.image.name == x:
                                    if la.name not in self.__class__.users['LAMP']:
                                        self.__class__.users['LAMP'].append(la.name)

            # Check World
            for wo in d.worlds:
                # Cycles
                if utils.cycles_exists():
                    if wo and wo.node_tree and wo.node_tree.nodes:
                        for no in wo.node_tree.nodes:
                            if no and \
                               no.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} and \
                               no.image and no.image.name == x:
                                if wo.name not in self.__class__.users['WORLD']:
                                    self.__class__.users['WORLD'].append(wo.name)

            # Check Textures
            for te in d.textures:
                if te and te.type =='IMAGE' and te.image:
                    name = te.image.name

                    if name == x and \
                       name not in self.__class__.users['TEXTURE'] :
                        self.__class__.users['TEXTURE'].append(te.name)

            # Check Modifiers in Objects
            for ob in d.objects:
                for mo in ob.modifiers:
                    if mo.type in {'UV_PROJECT'}:
                        image = mo.image

                        if mo and image and image.name == x:
                            name = '"{0}" modifier in {1}'.format(mo.name, ob.name)
                            if name not in self.__class__.users['MODIFIER']:
                                self.__class__.users['MODIFIER'].append(name)

            # Check Background Images in Viewports
            for scr in d.screens:
                for ar in scr.areas:
                    if ar.type == 'VIEW_3D':
                        if ar.spaces and \
                           ar.spaces.active and \
                           ar.spaces.active.background_images:
                            for bg in ar.spaces.active.background_images:
                                image = bg.image

                                if bg and image and image.name == x:
                                    name = 'Background for 3D Viewport in Screen "{0}"'\
                                            .format(scr.name)
                                    if name not in self.__class__.users['VIEW3D']:
                                        self.__class__.users['VIEW3D'].append(name)

            # Check the Compositor
            for sce in d.scenes:
                if sce.node_tree and sce.node_tree.nodes:
                    nodes = []

                    for nd in sce.node_tree.nodes:
                        if nd.type == 'IMAGE':
                            nodes.append(nd)
                        elif nd.type == 'GROUP':
                            if nd.node_tree and nd.node_tree.nodes:
                                for ng in nd.node_tree.nodes:
                                    if ng.type == 'IMAGE':
                                        nodes.append(ng)

                        for no in nodes:
                            if no.image and no.image.name == x:

                                links = False

                                for o in no.outputs:
                                    if o.links:
                                        links = True

                                name = 'Node {0} in Compositor (Scene "{1}"){2}'.format(
                                        no.name,
                                        sce.name,
                                        '' if links else ' (unconnected)')

                                if name not in self.__class__.users['NODETREE']:
                                    self.__class__.users['NODETREE'].append(name)

        # MATERIAL TYPE
        if dtype == 'MATERIAL':
            # Check Materials
            for ob in d.objects:
                for ma in ob.material_slots:
                    if ma.name == x:
                        if ma not in self.__class__.users['OBJECT_DATA']:
                            self.__class__.users['OBJECT_DATA'].append(ob)

                        if ob.library:
                            self.__class__.libraries.append(ob.library.filepath)

        # VERTEX COLOR TYPE
        elif dtype == 'GROUP_VCOL':
            # Check VCOL in Meshes
            for ob in bpy.data.objects:
                if ob.type == 'MESH':
                    for v in ob.data.vertex_colors:
                        if v.name == x:
                            name = '{0}'.format(ob.name)

                            if name not in self.__class__.users['MESH_DATA']:
                                self.__class__.users['MESH_DATA'].append(name)

            # Check VCOL in Materials
            for ma in d.materials:
                # Cycles
                if utils.cycles_exists():
                    if ma and ma.node_tree and ma.node_tree.nodes:
                        for no in ma.node_tree.nodes:
                            if no and no.type in {'ATTRIBUTE'}:
                                if no.attribute_name == x:
                                    objects = []

                                    for ob in d.objects:
                                        if ma.name in ob.material_slots:
                                            objects.append(ob.name)

                                    if objects:
                                        name = '{0} in object: {1}'.format(ma.name, objects)
                                    else:
                                        name = '{0} (unassigned)'.format(ma.name)

                                    if name not in self.__class__.users['MATERIAL']:
                                        self.__class__.users['MATERIAL'].append(name)


        self.__class__.libraries = sorted(list(set(self.__class__.libraries)))

        count_lib = 0

        # Print on console
        empty = True

        for t in self.__class__.users:
            if self.__class__.users[t]:
                empty = False
                print('\n== {0} {1} use {2} "{3}" ==\n'.format(
                        len(self.__class__.users[t]),
                        t,
                        dtype,
                        x))
                for p in self.__class__.users[t]:
                    print(' {0}'.format(p))

        if self.__class__.libraries:
            print("\n* Check %s:\n" %
                 ("this library" if len(self.__class__.libraries) == 1
                  else "these libraries"))

            for libs in self.__class__.libraries:
                print('%02d. %s' % (
                    count_lib + 1, self.__class__.libraries[count_lib]))
                count_lib += 1
            print("\n")

        if empty:
            print('\n== No users for {0} ==\n'.format(x))

        #print('Type: {0}'.format(context.scene.amth_datablock_types))
        #print('X: {0}'.format(x))

        return {"FINISHED"}


class AMTH_SCENE_OT_list_users_for_x_clear(bpy.types.Operator):

    """Clear the list below"""
    bl_idname = "scene.amth_list_users_for_x_clear"
    bl_label = "Clear Users Lists for X"

    def execute(self, context):
        AMTH_SCENE_OT_list_users_for_x.users = {}
        print("* Cleared Users List for Datablock")
        return {"FINISHED"}


class AMTH_SCENE_OT_blender_instance_open(bpy.types.Operator):

    """Open in a new Blender instance"""
    bl_idname = "scene.blender_instance_open"
    bl_label = "Open Blender Instance"
    filepath = bpy.props.StringProperty()

    def execute(self, context):
        if self.filepath:
            filepath = os.path.normpath(bpy.path.abspath(self.filepath))

            import subprocess
            try:
                subprocess.Popen([bpy.app.binary_path, filepath])
            except:
                print("Error on the new Blender instance")
                import traceback
                traceback.print_exc()

        return {"FINISHED"}


class AMTH_SCENE_PT_scene_debug(bpy.types.Panel):

    """Scene Debug"""
    bl_label = "Scene Debug"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="RADIO")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        images = bpy.data.images
        images_missing = []
        list_missing_images = scene.amaranth_debug_scene_list_missing_images
        materials = AMTH_SCENE_OT_cycles_shader_list_nodes.materials
        materials_count = len(AMTH_SCENE_OT_cycles_shader_list_nodes.materials)
        missing_material_slots_obs = AMTH_SCENE_OT_list_missing_material_slots.objects
        missing_material_slots_count = len(
            AMTH_SCENE_OT_list_missing_material_slots.objects)
        missing_material_slots_lib = AMTH_SCENE_OT_list_missing_material_slots.libraries
        engine = scene.render.engine

        # List Missing Images
        box = layout.box()
        row = box.row(align=True)
        split = row.split()
        col = split.column()

        if images:

            for im in images:
                if im.type not in ("UV_TEST", "RENDER_RESULT", "COMPOSITING"):
                    if not im.packed_file and \
                       not os.path.exists(bpy.path.abspath(im.filepath, library=im.library)):
                        images_missing.append(["%s%s [%s]%s" % (
                            "[L] " if im.library else "",
                            im.name, im.users,
                            " [F]" if im.use_fake_user else ""),
                            im.filepath if im.filepath else "No Filepath",
                            im.library.filepath if im.library else ""])

            if images_missing:
                row = col.row(align=True)
                row.alignment = "LEFT"
                row.prop(
                    scene,
                    "amaranth_debug_scene_list_missing_images",
                    icon="%s" %
                    "TRIA_DOWN" if list_missing_images else "TRIA_RIGHT",
                    emboss=False)

                split = split.split()
                col = split.column()

                col.label(text="%s missing %s" % (
                          str(len(images_missing)),
                          'image' if len(images_missing) == 1 else "images"),
                          icon="ERROR")

                if list_missing_images:
                    col = box.column(align=True)
                    for mis in images_missing:
                        row = col.row(align=True)
                        row.alignment = "LEFT"
                        row.label(
                            text=mis[0],
                            icon="IMAGE_DATA")
                        # XXX TODO // make clicking on image work (needs new op to set x)
                        # row.operator(
                        #     AMTH_SCENE_OT_list_users_for_x.bl_idname,
                        #     text=mis[0],
                        #     icon="IMAGE_DATA",
                        #     emboss=False).name = mis[0][:-4]

                        row = col.row(align=True)
                        row.label(text=mis[1], icon="LIBRARY_DATA_DIRECT")
                        if mis[2]:
                            row = col.row(align=True)
                            row.alignment = "LEFT"
                            row.operator(
                                AMTH_SCENE_OT_blender_instance_open.bl_idname,
                                text=mis[2],
                                icon="LINK_BLEND",
                                emboss=False).filepath = mis[2]
                        col.separator()
            else:
                row = col.row(align=True)
                row.alignment = "LEFT"
                row.label(
                    text="Great! No missing images", icon="RIGHTARROW_THIN")

                split = split.split()
                col = split.column()

                col.label(text="%s %s loading correctly" % (
                          str(len(images)),
                          "image" if len(images) == 1 else "images"),
                          icon="IMAGE_DATA")
        else:
            row = col.row(align=True)
            row.alignment = "LEFT"
            row.label(text="No images loaded yet", icon="RIGHTARROW_THIN")

        # List Cycles Materials by Shader
        if utils.cycles_exists() and engine == "CYCLES":
            box = layout.box()
            split = box.split()
            col = split.column(align=True)
            col.prop(scene, "amaranth_cycles_node_types",
                     icon="MATERIAL")

            row = split.row(align=True)
            row.operator(AMTH_SCENE_OT_cycles_shader_list_nodes.bl_idname,
                         icon="SORTSIZE",
                         text="List Materials Using Shader")
            if materials_count != 0:
                row.operator(
                    AMTH_SCENE_OT_cycles_shader_list_nodes_clear.bl_idname,
                    icon="X", text="")
            col.separator()

            try:
                materials
            except NameError:
                pass
            else:
                if materials_count != 0:
                    col = box.column(align=True)
                    count = 0
                    col.label(
                        text="%s %s found" %
                        (materials_count,
                         "material" if materials_count == 1 else "materials"),
                        icon="INFO")
                    for mat in materials:
                        count += 1
                        col.label(
                            text="%s" %
                            (materials[
                                count -
                                1]),
                            icon="MATERIAL")

        # List Missing Node Trees
        box = layout.box()
        row = box.row(align=True)
        split = row.split()
        col = split.column(align=True)

        split = col.split()
        split.label(text="Node Links")
        split.operator(AMTH_SCENE_OT_list_missing_node_links.bl_idname,
                       icon="NODETREE")

        if AMTH_SCENE_OT_list_missing_node_links.count_groups != 0 or \
                AMTH_SCENE_OT_list_missing_node_links.count_images != 0 or \
                AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked != 0:
            col.label(text="Warning! Check Console", icon="ERROR")

        if AMTH_SCENE_OT_list_missing_node_links.count_groups != 0:
            col.label(
                text="%s" %
                ("%s node %s missing link" %
                 (str(
                     AMTH_SCENE_OT_list_missing_node_links.count_groups),
                     "group" if AMTH_SCENE_OT_list_missing_node_links.count_groups == 1 else "groups")),
                icon="NODETREE")
        if AMTH_SCENE_OT_list_missing_node_links.count_images != 0:
            col.label(
                text="%s" %
                ("%s image %s missing link" %
                 (str(
                     AMTH_SCENE_OT_list_missing_node_links.count_images),
                     "node" if AMTH_SCENE_OT_list_missing_node_links.count_images == 1 else "nodes")),
                icon="IMAGE_DATA")

        if AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked != 0:
            col.label(
                text="%s" %
                ("%s image %s with no output conected" %
                 (str(
                     AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked),
                     "node" if AMTH_SCENE_OT_list_missing_node_links.count_image_node_unlinked == 1 else "nodes")),
                icon="NODE")

        # List Empty Materials Slots
        box = layout.box()
        split = box.split()
        col = split.column(align=True)
        col.label(text="Material Slots")

        row = split.row(align=True)
        row.operator(AMTH_SCENE_OT_list_missing_material_slots.bl_idname,
                     icon="MATERIAL",
                     text="List Empty Materials Slots")
        if missing_material_slots_count != 0:
            row.operator(
                AMTH_SCENE_OT_list_missing_material_slots_clear.bl_idname,
                icon="X", text="")
        col.separator()

        try:
            missing_material_slots_obs
        except NameError:
            pass
        else:
            if missing_material_slots_count != 0:
                col = box.column(align=True)
                count = 0
                count_lib = 0
                col.label(
                    text="%s %s with empty material slots found" %
                    (missing_material_slots_count,
                     "object" if missing_material_slots_count == 1 else "objects"),
                    icon="INFO")

                for obs in missing_material_slots_obs:
                    count += 1

                    row = col.row()
                    row.alignment = "LEFT"
                    row.label(
                        text="%s" % missing_material_slots_obs[count - 1],
                        icon="OBJECT_DATA")

                if missing_material_slots_lib:
                    col.separator()
                    col.label("Check %s:" % (
                        "this library" if
                        len(missing_material_slots_lib) == 1
                        else "these libraries"))

                    for libs in missing_material_slots_lib:
                        count_lib += 1
                        row = col.row(align=True)
                        row.alignment = "LEFT"
                        row.operator(
                            AMTH_SCENE_OT_blender_instance_open.bl_idname,
                            text=missing_material_slots_lib[
                                count_lib - 1],
                            icon="LINK_BLEND",
                            emboss=False).filepath = missing_material_slots_lib[
                            count_lib - 1]


        # List Users for Datablock
        list_users = AMTH_SCENE_OT_list_users_for_x.users
        list_users_libs = AMTH_SCENE_OT_list_users_for_x.libraries

        box = layout.box()
        row = box.row(align=True)
        row.label(text="List Users for Datablock")

        col = box.column(align=True)
        split = col.split()
        row = split.row(align=True)
        row.prop(scene, "amth_datablock_types",
                    icon=scene.amth_datablock_types,
                    text="")

        row.operator_menu_enum("scene.amth_list_users_for_x_type",
                                       "list_type_select",
                                       text=scene.amth_list_users_for_x_name)

        row = split.row(align=True)
        row.enabled = True if scene.amth_list_users_for_x_name else False
        row.operator(AMTH_SCENE_OT_list_users_for_x.bl_idname).name = scene.amth_list_users_for_x_name
        if list_users:
            row.operator(
                AMTH_SCENE_OT_list_users_for_x_clear.bl_idname,
                icon="X", text="")

        try:
            list_users
        except NameError:
            pass
        else:
            if list_users:
                empty = True
                col = box.column(align=True)
                for t in list_users:
                    if list_users[t]:
                        empty = False
                        for ma in list_users[t]:
                            row = col.row(align=True)
                            row.alignment = "LEFT"
                            if t == 'OBJECT_DATA':
                                row.operator(
                                    AMTH_SCENE_OT_amaranth_object_select.bl_idname,
                                    text="%s %s%s" %
                                    (" [L] " if ma.library else "",
                                     ma.name,
                                     "" if ma.name in context.scene.objects else " [Not in Scene]"),
                                    icon=t,
                                    emboss=False).object = ma.name
                            else:
                                row.label(text=ma,
                                          icon=t)
                if empty:
                    row = col.row(align=True)
                    row.alignment = "LEFT"
                    row.label(text="No users for '{0}'".format(
                              scene.amth_list_users_for_x_name),
                              icon='INFO')

                if list_users_libs:
                    count_lib = 0

                    col.separator()
                    col.label("Check %s:" % (
                        "this library" if
                        len(list_users_libs) == 1
                        else "these libraries"))

                    for libs in list_users_libs:
                        count_lib += 1
                        row = col.row(align=True)
                        row.alignment = "LEFT"
                        row.operator(
                            AMTH_SCENE_OT_blender_instance_open.bl_idname,
                            text=list_users_libs[
                                count_lib - 1],
                            icon="LINK_BLEND",
                            emboss=False).filepath = list_users_libs[
                            count_lib - 1]

class AMTH_LightersCorner(bpy.types.Panel):

    """The Lighters Panel"""
    bl_label = "Lighter's Corner"
    bl_idname = "AMTH_SCENE_PT_lighters_corner"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        preferences = context.user_preferences.addons["amaranth"].preferences

        return preferences.use_lighters_corner

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="LAMP_SUN")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        objects = bpy.data.objects
        ob_act = context.active_object
        lamps = bpy.data.lamps
        list_meshlights = scene.amaranth_lighterscorner_list_meshlights
        engine = scene.render.engine

        if utils.cycles_exists():
            layout.prop(scene, "amaranth_lighterscorner_list_meshlights")

        box = layout.box()
        if lamps:
            if objects:
                row = box.row(align=True)
                split = row.split(percentage=0.45)
                col = split.column()

                col.label(text="Name")

                if engine in ["CYCLES", "BLENDER_RENDER"]:
                    if engine == "BLENDER_RENDER":
                        split = split.split(percentage=0.7)
                    else:
                        split = split.split(percentage=0.27)
                    col = split.column()
                    col.label(text="Samples")

                if utils.cycles_exists() and engine == "CYCLES":
                    split = split.split(percentage=0.2)
                    col = split.column()
                    col.label(text="Size")

                split = split.split(percentage=1.0)
                col = split.column()
                col.label(text="%sRender Visibility" %
                          "Rays /" if utils.cycles_exists() else "")

                for ob in objects:
                    is_lamp = ob.type == "LAMP"
                    is_emission = True if utils.cycles_is_emission(
                        context, ob) and list_meshlights else False

                    if ob and is_lamp or is_emission:
                        lamp = ob.data
                        if utils.cycles_exists():
                            clamp = ob.data.cycles
                            visibility = ob.cycles_visibility

                        row = box.row(align=True)
                        split = row.split(percentage=1.0)
                        col = split.column()
                        row = col.row(align=True)
                        col.active = ob == ob_act
                        row.label(
                            icon="%s" %
                            ("LAMP_%s" %
                             ob.data.type if is_lamp else "MESH_GRID"))
                        split = row.split(percentage=.45)
                        col = split.column()
                        row = col.row(align=True)
                        row.alignment = "LEFT"
                        row.active = True
                        row.operator(
                            AMTH_SCENE_OT_amaranth_object_select.bl_idname,
                            text="%s %s%s" %
                            (" [L] " if ob.library else "",
                             ob.name,
                             "" if ob.name in context.scene.objects else " [Not in Scene]"),
                            emboss=False).object = ob.name
                        if ob.library:
                            row = col.row(align=True)
                            row.alignment = "LEFT"
                            row.operator(
                                AMTH_SCENE_OT_blender_instance_open.bl_idname,
                                text=ob.library.filepath,
                                icon="LINK_BLEND",
                                emboss=False).filepath = ob.library.filepath

                        if utils.cycles_exists() and engine == "CYCLES":
                            split = split.split(percentage=0.25)
                            col = split.column()
                            if is_lamp:
                                if scene.cycles.progressive == "BRANCHED_PATH":
                                    col.prop(clamp, "samples", text="")
                                if scene.cycles.progressive == "PATH":
                                    col.label(text="N/A")
                            else:
                                col.label(text="N/A")

                        if engine == "BLENDER_RENDER":
                            split = split.split(percentage=0.7)
                            col = split.column()
                            if is_lamp:
                                if lamp.type == "HEMI":
                                    col.label(text="Not Available")
                                elif lamp.type == "AREA" and lamp.shadow_method == "RAY_SHADOW":
                                    row = col.row(align=True)
                                    row.prop(
                                        lamp, "shadow_ray_samples_x", text="X")
                                    if lamp.shape == "RECTANGLE":
                                        row.prop(
                                            lamp,
                                            "shadow_ray_samples_y",
                                            text="Y")
                                elif lamp.shadow_method == "RAY_SHADOW":
                                    col.prop(
                                        lamp,
                                        "shadow_ray_samples",
                                        text="Ray Samples")
                                elif lamp.shadow_method == "BUFFER_SHADOW":
                                    col.prop(
                                        lamp,
                                        "shadow_buffer_samples",
                                        text="Buffer Samples")
                                else:
                                    col.label(text="No Shadow")
                            else:
                                col.label(text="N/A")

                        if utils.cycles_exists() and engine == "CYCLES":
                            split = split.split(percentage=0.2)
                            col = split.column()
                            if is_lamp:
                                if lamp.type in ["POINT", "SUN", "SPOT"]:
                                    col.label(
                                        text="%.2f" % lamp.shadow_soft_size)
                                elif lamp.type == "HEMI":
                                    col.label(text="N/A")
                                elif lamp.type == "AREA" and lamp.shape == "RECTANGLE":
                                    col.label(
                                        text="%.2fx%.2f" %
                                        (lamp.size, lamp.size_y))
                                else:
                                    col.label(text="%.2f" % lamp.size)
                            else:
                                col.label(text="N/A")

                        split = split.split(percentage=1.0)
                        col = split.column()
                        row = col.row(align=True)
                        if utils.cycles_exists():
                            row.prop(visibility, "camera", text="")
                            row.prop(visibility, "diffuse", text="")
                            row.prop(visibility, "glossy", text="")
                            row.prop(visibility, "shadow", text="")
                            row.separator()
                        row.prop(ob, "hide", text="", emboss=False)
                        row.prop(ob, "hide_render", text="", emboss=False)
        else:
            box.label(text="No Lamps", icon="LAMP_DATA")


classes = {
    AMTH_SCENE_PT_scene_debug,
    AMTH_SCENE_OT_blender_instance_open,
    AMTH_SCENE_OT_amaranth_object_select,
    AMTH_SCENE_OT_list_missing_node_links,
    AMTH_SCENE_OT_list_missing_material_slots,
    AMTH_SCENE_OT_list_missing_material_slots_clear,
    AMTH_SCENE_OT_cycles_shader_list_nodes,
    AMTH_SCENE_OT_cycles_shader_list_nodes_clear,
    AMTH_SCENE_OT_list_users_for_x,
    AMTH_SCENE_OT_list_users_for_x_type,
    AMTH_SCENE_OT_list_users_for_x_clear,
    AMTH_LightersCorner
}

def register():
    init()

    for cls in classes:
        bpy.utils.register_class(cls)

    from bpy.types import Scene

    bpy.types.Scene.amth_list_users_for_x_name = bpy.props.StringProperty(
                                                    default="",
                                                    name="Name",
                                                    description="Which datablock type to look for")

def unregister():
    clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    from bpy.types import Scene

    del Scene.amth_list_users_for_x_name
