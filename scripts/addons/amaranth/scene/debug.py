# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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

Under the "Scene Debug" panel in Scene properties.

* Lighter's Corner
This is an UI List of Lights in the scene(s).
It allows you to quickly see how many lights you have, select them by
clicking on their name, see their type (icon), samples number (if using
Branched Path Tracing), size, and change their visibility.

"""

# TODO: module cleanup! maybe break it up in a package
#     dicts instead of if, elif, else all over the place.
#     helper functions instead of everything on the execute method.
#     str.format() + dicts instead of inline % op all over the place.
#     remove/manage debug print calls.
#     avoid duplicate code/patterns through helper functions.

import os
import bpy
from amaranth import utils
from bpy.types import (
        Operator,
        Panel,
        UIList,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        CollectionProperty,
        EnumProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        )

# default string used in the List Users for Datablock section menus
USER_X_NAME_EMPTY = "Data Block not selected/existing"


class AMTH_store_data():
    # used by: AMTH_SCENE_OT_list_users_for_x operator
    users = {
        'OBJECT_DATA': [],         # Store Objects with Material
        'MATERIAL': [],            # Materials (Node tree)
        'LIGHT': [],               # Lights
        'WORLD': [],               # World
        'TEXTURE': [],             # Textures (Psys, Brushes)
        'MODIFIER': [],            # Modifiers
        'MESH_DATA': [],           # Vertex Colors
        'OUTLINER_OB_CAMERA': [],  # Background Images in Cameras
        'OUTLINER_OB_EMPTY': [],   # Empty type Image
        'NODETREE': [],            # Compositor
        }
    libraries = []                 # Libraries x type

    # used by: AMTH_SCENE_OT_list_missing_material_slots operator
    obj_mat_slots = []             # Missing material slots
    obj_mat_slots_lib = []         # Libraries with missing material slots

    # used by: AMTH_SCENE_OT_cycles_shader_list_nodes operator
    mat_shaders = []               # Materials that use a specific shader

    # used by : AMTH_SCENE_OT_list_missing_node_links operator
    count_groups = 0               # Missing node groups count
    count_images = 0               # Missing node images
    count_image_node_unlinked = 0  # Unlinked Image nodes


def call_update_datablock_type(self, context):
    try:
        # Note: this is pretty weak, but updates the operator enum selection
        bpy.ops.scene.amth_list_users_for_x_type(list_type_select='0')
    except:
        pass


def init():
    scene = bpy.types.Scene

    scene.amaranth_lighterscorner_list_meshlights = BoolProperty(
        default=False,
        name="List Meshlights",
        description="Include light emitting meshes on the list"
    )
    amth_datablock_types = (
        ("IMAGE_DATA", "Image", "Image Datablocks", 0),
        ("MATERIAL", "Material", "Material Datablocks", 1),
        ("GROUP_VCOL", "Vertex Colors", "Vertex Color Layers", 2),
    )
    scene.amth_datablock_types = EnumProperty(
        items=amth_datablock_types,
        name="Type",
        description="Datablock Type",
        default="MATERIAL",
        update=call_update_datablock_type,
        options={"SKIP_SAVE"}
    )
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
            ('BSDF_PRINCIPLED', 'Principled BSDF', "", 19),
        )
        scene.amaranth_cycles_node_types = EnumProperty(
            items=cycles_shader_node_types,
            name="Shader"
        )


def clear():
    props = (
        "amaranth_cycles_node_types",
        "amaranth_lighterscorner_list_meshlights",
    )
    wm = bpy.context.window_manager
    for p in props:
        if wm.get(p):
            del wm[p]


def print_with_count_list(text="", send_list=[]):
    if text:
        print("\n* {}\n".format(text))
    if not send_list:
        print("List is empty, no items to display")
        return

    for i, entry in enumerate(send_list):
        print('{:02d}. {}'.format(i + 1, send_list[i]))
    print("\n")


def print_grammar(line="", single="", multi="", cond=[]):
    phrase = single if len(cond) == 1 else multi
    print("\n* {} {}:\n".format(line, phrase))


def reset_global_storage(what="NONE"):
    if what == "NONE":
        return

    if what == "XTYPE":
        for user in AMTH_store_data.users:
            AMTH_store_data.users[user] = []
        AMTH_store_data.libraries = []

    elif what == "MAT_SLOTS":
        AMTH_store_data.obj_mat_slots[:] = []
        AMTH_store_data.obj_mat_slots_lib[:] = []

    elif what == "NODE_LINK":
        AMTH_store_data.obj_mat_slots[:] = []
        AMTH_store_data.count_groups = 0
        AMTH_store_data.count_images = 0
        AMTH_store_data.count_image_node_unlinked = 0

    elif what == "SHADER":
        AMTH_store_data.mat_shaders[:] = []


class AMTH_SCENE_OT_cycles_shader_list_nodes(Operator):
    """List Cycles materials containing a specific shader"""
    bl_idname = "scene.cycles_list_nodes"
    bl_label = "List Materials"

    @classmethod
    def poll(cls, context):
        return utils.cycles_exists() and utils.cycles_active(context)

    def execute(self, context):
        node_type = context.scene.amaranth_cycles_node_types
        roughness = False
        shaders_roughness = ("BSDF_GLOSSY", "BSDF_DIFFUSE", "BSDF_GLASS")

        reset_global_storage("SHADER")

        print("\n=== Cycles Shader Type: {} === \n".format(node_type))

        for ma in bpy.data.materials:
            if not ma.node_tree:
                continue

            nodes = ma.node_tree.nodes
            print_unconnected = (
                "Note: \nOutput from \"{}\" node in material \"{}\" "
                "not connected\n".format(node_type, ma.name)
                )

            for no in nodes:
                if no.type == node_type:
                    for ou in no.outputs:
                        if ou.links:
                            connected = True
                            if no.type in shaders_roughness:
                                roughness = "R: {:.4f}".format(
                                    no.inputs["Roughness"].default_value
                                    )
                            else:
                                roughness = False
                        else:
                            connected = False
                            print(print_unconnected)

                        if ma.name not in AMTH_store_data.mat_shaders:
                            AMTH_store_data.mat_shaders.append(
                                "%s%s [%s] %s%s%s" %
                                ("[L] " if ma.library else "",
                                 ma.name,
                                 ma.users,
                                 "[F]" if ma.use_fake_user else "",
                                 " - [%s]" %
                                 roughness if roughness else "",
                                 " * Output not connected" if not connected else "")
                                )
                elif no.type == "GROUP":
                    if no.node_tree:
                        for nog in no.node_tree.nodes:
                            if nog.type == node_type:
                                for ou in nog.outputs:
                                    if ou.links:
                                        connected = True
                                        if nog.type in shaders_roughness:
                                            roughness = "R: {:.4f}".format(
                                                nog.inputs["Roughness"].default_value
                                                )
                                        else:
                                            roughness = False
                                    else:
                                        connected = False
                                        print(print_unconnected)

                                    if ma.name not in AMTH_store_data.mat_shaders:
                                        AMTH_store_data.mat_shaders.append(
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
                                                " * Output not connected" if not connected else "")
                                            )
                AMTH_store_data.mat_shaders = sorted(list(set(AMTH_store_data.mat_shaders)))

        message = "No materials with nodes type {} found".format(node_type)
        if len(AMTH_store_data.mat_shaders) > 0:
            message = "A total of {} {} using {} found".format(
                    len(AMTH_store_data.mat_shaders),
                    "material" if len(AMTH_store_data.mat_shaders) == 1 else "materials",
                    node_type)
            print_with_count_list(send_list=AMTH_store_data.mat_shaders)

        self.report({'INFO'}, message)
        AMTH_store_data.mat_shaders = sorted(list(set(AMTH_store_data.mat_shaders)))

        return {"FINISHED"}


class AMTH_SCENE_OT_amaranth_object_select(Operator):
    """Select object"""
    bl_idname = "scene.amaranth_object_select"
    bl_label = "Select Object"

    object_name: StringProperty()

    def execute(self, context):
        if not (self.object_name and self.object_name in bpy.data.objects):
            self.report({'WARNING'},
                        "Object with the given name could not be found. Operation Cancelled")
            return {"CANCELLED"}

        obj = bpy.data.objects[self.object_name]

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {"FINISHED"}


class AMTH_SCENE_OT_list_missing_node_links(Operator):
    """Print a list of missing node links"""
    bl_idname = "scene.list_missing_node_links"
    bl_label = "List Missing Node Links"

    def execute(self, context):
        missing_groups = []
        missing_images = []
        image_nodes_unlinked = []
        libraries = []

        reset_global_storage(what="NODE_LINK")

        for ma in bpy.data.materials:
            if not ma.node_tree:
                continue

            for no in ma.node_tree.nodes:
                if no.type == "GROUP":
                    if not no.node_tree:
                        AMTH_store_data.count_groups += 1

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
                             ",  ".join(users_ngroup) if users_ngroup else "")
                            )
                        if ma.library:
                            libraries.append(ma.library.filepath)

                if no.type == "TEX_IMAGE":

                    outputs_empty = not no.outputs["Color"].is_linked and \
                                    not no.outputs["Alpha"].is_linked

                    if no.image:
                        image_path_exists = os.path.exists(
                                bpy.path.abspath(
                                no.image.filepath,
                                library=no.image.library)
                                )

                    if outputs_empty or not no.image or not image_path_exists:

                        users_images = []

                        for ob in bpy.data.objects:
                            if ob.material_slots and ma.name in ob.material_slots:
                                users_images.append("%s%s%s" % (
                                    "[L] " if ob.library else "",
                                    "[F] " if ob.use_fake_user else "",
                                    ob.name))

                        if outputs_empty:
                            AMTH_store_data.count_image_node_unlinked += 1

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
                            AMTH_store_data.count_images += 1

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
            ("No" if AMTH_store_data.count_images == 0 else str(
                AMTH_store_data.count_images),
                "node" if AMTH_store_data.count_images == 1 else "nodes",
                "no" if AMTH_store_data.count_groups == 0 else str(
                    AMTH_store_data.count_groups),
                "group" if AMTH_store_data.count_groups == 1 else "groups",
                "no" if AMTH_store_data.count_image_node_unlinked == 0 else str(
                    AMTH_store_data.count_image_node_unlinked),
                "node" if AMTH_store_data.count_groups == 1 else "nodes")
            )
        # List Missing Node Groups
        if missing_groups:
            print_with_count_list("Missing Node Group Links", missing_groups)

        # List Missing Image Nodes
        if missing_images:
            print_with_count_list("Missing Image Nodes Link", missing_images)

        # List Image Nodes with its outputs unlinked
        if image_nodes_unlinked:
            print_with_count_list("Image Nodes Unlinked", image_nodes_unlinked)

        if missing_groups or missing_images or image_nodes_unlinked:
            if libraries:
                print_grammar("That's bad, run check", "this library", "these libraries", libraries)
                print_with_count_list(send_list=libraries)
        else:
            self.report({"INFO"}, "Yay! No missing node links")

        if missing_groups and missing_images:
            self.report(
                {"WARNING"},
                "%d missing image %s and %d missing node %s found" %
                (AMTH_store_data.count_images,
                 "node" if AMTH_store_data.count_images == 1 else "nodes",
                 AMTH_store_data.count_groups,
                 "group" if AMTH_store_data.count_groups == 1 else "groups")
                )

        return {"FINISHED"}


class AMTH_SCENE_OT_list_missing_material_slots(Operator):
    """List objects with empty material slots"""
    bl_idname = "scene.list_missing_material_slots"
    bl_label = "List Empty Material Slots"

    def execute(self, context):
        reset_global_storage("MAT_SLOTS")

        for ob in bpy.data.objects:
            for ma in ob.material_slots:
                if not ma.material:
                    AMTH_store_data.obj_mat_slots.append('{}{}'.format(
                        '[L] ' if ob.library else '', ob.name))
                    if ob.library:
                        AMTH_store_data.obj_mat_slots_lib.append(ob.library.filepath)

        AMTH_store_data.obj_mat_slots = sorted(list(set(AMTH_store_data.obj_mat_slots)))
        AMTH_store_data.obj_mat_slots_lib = sorted(list(set(AMTH_store_data.obj_mat_slots_lib)))

        if len(AMTH_store_data.obj_mat_slots) == 0:
            self.report({"INFO"},
                        "No objects with empty material slots found")
            return {"FINISHED"}

        print(
            "\n* A total of {} {} with empty material slots was found \n".format(
            len(AMTH_store_data.obj_mat_slots),
            "object" if len(AMTH_store_data.obj_mat_slots) == 1 else "objects")
            )
        print_with_count_list(send_list=AMTH_store_data.obj_mat_slots)

        if AMTH_store_data.obj_mat_slots_lib:
            print_grammar("Check", "this library", "these libraries",
                          AMTH_store_data.obj_mat_slots_lib
            )
            print_with_count_list(send_list=AMTH_store_data.obj_mat_slots_lib)

        return {"FINISHED"}


class AMTH_SCENE_OT_list_users_for_x_type(Operator):
    bl_idname = "scene.amth_list_users_for_x_type"
    bl_label = "Select"
    bl_description = "Select Datablock Name"

    @staticmethod
    def fill_where():
        where = []
        data_block = bpy.context.scene.amth_datablock_types

        if data_block == 'IMAGE_DATA':
            for im in bpy.data.images:
                if im.name not in {'Render Result', 'Viewer Node'}:
                    where.append(im)

        elif data_block == 'MATERIAL':
            where = bpy.data.materials

        elif data_block == 'GROUP_VCOL':
            for ob in bpy.data.objects:
                if ob.type == 'MESH':
                    for v in ob.data.vertex_colors:
                        if v and v not in where:
                            where.append(v)
            where = list(set(where))

        return where

    def avail(self, context):
        datablock_type = bpy.context.scene.amth_datablock_types
        where = AMTH_SCENE_OT_list_users_for_x_type.fill_where()
        items = [(str(i), x.name, x.name, datablock_type, i) for i, x in enumerate(where)]
        items = sorted(list(set(items)))
        if not items:
            items = [('0', USER_X_NAME_EMPTY, USER_X_NAME_EMPTY, "INFO", 0)]
        return items

    list_type_select: EnumProperty(
            items=avail,
            name="Available",
            options={"SKIP_SAVE"}
            )

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.amth_datablock_types

    def execute(self, context):
        where = self.fill_where()
        bpy.context.scene.amth_list_users_for_x_name = \
                where[int(self.list_type_select)].name if where else USER_X_NAME_EMPTY

        return {'FINISHED'}


class AMTH_SCENE_OT_list_users_for_x(Operator):
    """List users for a particular datablock"""
    bl_idname = "scene.amth_list_users_for_x"
    bl_label = "List Users for Datablock"

    name: StringProperty()

    def execute(self, context):
        d = bpy.data
        x = self.name if self.name else context.scene.amth_list_users_for_x_name

        if USER_X_NAME_EMPTY in x:
            self.report({'INFO'},
                        "Please select a DataBlock name first. Operation Cancelled")
            return {"CANCELLED"}

        dtype = context.scene.amth_datablock_types

        reset_global_storage("XTYPE")

        # IMAGE TYPE
        if dtype == 'IMAGE_DATA':
            # Check Materials
            for ma in d.materials:
                # Cycles
                if utils.cycles_exists():
                    if ma and ma.node_tree and ma.node_tree.nodes:
                        materials = []

                        for nd in ma.node_tree.nodes:
                            if nd and nd.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'}:
                                materials.append(nd)

                            if nd and nd.type == 'GROUP':
                                if nd.node_tree and nd.node_tree.nodes:
                                    for ng in nd.node_tree.nodes:
                                        if ng.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'}:
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

                                    if name not in AMTH_store_data.users['MATERIAL']:
                                        AMTH_store_data.users['MATERIAL'].append(name)

            # Check Lights
            for la in d.lights:
                # Cycles
                if utils.cycles_exists():
                    if la and la.node_tree and la.node_tree.nodes:
                        for no in la.node_tree.nodes:
                            if no and \
                                   no.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'} and \
                                   no.image and no.image.name == x:
                                if la.name not in AMTH_store_data.users['LIGHT']:
                                    AMTH_store_data.users['LIGHT'].append(la.name)

            # Check World
            for wo in d.worlds:
                # Cycles
                if utils.cycles_exists():
                    if wo and wo.node_tree and wo.node_tree.nodes:
                        for no in wo.node_tree.nodes:
                            if no and \
                                   no.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'} and \
                                   no.image and no.image.name == x:
                                if wo.name not in AMTH_store_data.users['WORLD']:
                                    AMTH_store_data.users['WORLD'].append(wo.name)

            # Check Textures
            for te in d.textures:
                if te and te.type == 'IMAGE' and te.image:
                    name = te.image.name

                    if name == x and \
                            name not in AMTH_store_data.users['TEXTURE']:
                        AMTH_store_data.users['TEXTURE'].append(te.name)

            # Check Modifiers in Objects
            for ob in d.objects:
                for mo in ob.modifiers:
                    if mo.type in {'UV_PROJECT'}:
                        image = mo.image

                        if mo and image and image.name == x:
                            name = '"{0}" modifier in {1}'.format(mo.name, ob.name)
                            if name not in AMTH_store_data.users['MODIFIER']:
                                AMTH_store_data.users['MODIFIER'].append(name)

            # Check Background Images in Cameras
            for ob in d.objects:
                if ob and ob.type == 'CAMERA' and ob.data.background_images:
                    for bg in ob.data.background_images:
                        image = bg.image

                        if bg and image and image.name == x:
                            name = 'Used as background for Camera "{0}"'\
                                    .format(ob.name)
                            if name not in AMTH_store_data.users['OUTLINER_OB_CAMERA']:
                                AMTH_store_data.users['OUTLINER_OB_CAMERA'].append(name)

            # Check Empties type Image
            for ob in d.objects:
                if ob and ob.type == 'EMPTY' and ob.image_user:
                    if ob.image_user.id_data.data:
                        image = ob.image_user.id_data.data

                        if image and image.name == x:
                            name = 'Used in Empty "{0}"'\
                                    .format(ob.name)
                            if name not in AMTH_store_data.users['OUTLINER_OB_EMPTY']:
                                AMTH_store_data.users['OUTLINER_OB_EMPTY'].append(name)

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

                                if name not in AMTH_store_data.users['NODETREE']:
                                    AMTH_store_data.users['NODETREE'].append(name)
        # MATERIAL TYPE
        if dtype == 'MATERIAL':
            # Check Materials - Note: build an object_check list as only strings are stored
            object_check = [d.objects[names] for names in AMTH_store_data.users['OBJECT_DATA'] if
                            names in d.objects]
            for ob in d.objects:
                for ma in ob.material_slots:
                    if ma.name == x:
                        if ma not in object_check:
                            AMTH_store_data.users['OBJECT_DATA'].append(ob.name)

                        if ob.library:
                            AMTH_store_data.libraries.append(ob.library.filepath)
        # VERTEX COLOR TYPE
        elif dtype == 'GROUP_VCOL':
            # Check VCOL in Meshes
            for ob in bpy.data.objects:
                if ob.type == 'MESH':
                    for v in ob.data.vertex_colors:
                        if v.name == x:
                            name = '{0}'.format(ob.name)

                            if name not in AMTH_store_data.users['MESH_DATA']:
                                AMTH_store_data.users['MESH_DATA'].append(name)
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

                                    if name not in AMTH_store_data.users['MATERIAL']:
                                        AMTH_store_data.users['MATERIAL'].append(name)

        AMTH_store_data.libraries = sorted(list(set(AMTH_store_data.libraries)))

        # Print on console
        empty = True
        for t in AMTH_store_data.users:
            if AMTH_store_data.users[t]:
                empty = False
                print('\n== {0} {1} use {2} "{3}" ==\n'.format(
                        len(AMTH_store_data.users[t]),
                        t,
                        dtype,
                        x))
                for p in AMTH_store_data.users[t]:
                    print(' {0}'.format(p))

        if AMTH_store_data.libraries:
            print_grammar("Check", "this library", "these libraries",
                          AMTH_store_data.libraries
                        )
            print_with_count_list(send_list=AMTH_store_data.libraries)

        if empty:
            self.report({'INFO'}, "No users for {}".format(x))

        return {"FINISHED"}


class AMTH_SCENE_OT_list_users_debug_clear(Operator):
    """Clear the list below"""
    bl_idname = "scene.amth_list_users_debug_clear"
    bl_label = "Clear Debug Panel lists"

    what: StringProperty(
            name="",
            default="NONE",
            options={'HIDDEN'}
            )

    def execute(self, context):
        reset_global_storage(self.what)

        return {"FINISHED"}


class AMTH_SCENE_OT_blender_instance_open(Operator):
    """Open in a new Blender instance"""
    bl_idname = "scene.blender_instance_open"
    bl_label = "Open Blender Instance"

    filepath: StringProperty()

    def execute(self, context):
        if self.filepath:
            filepath = os.path.normpath(bpy.path.abspath(self.filepath))

            import subprocess
            try:
                subprocess.Popen([bpy.app.binary_path, filepath])
            except:
                print("Error opening a new Blender instance")
                import traceback
                traceback.print_exc()

        return {"FINISHED"}


class AMTH_SCENE_OT_Collection_List_Refresh(Operator):
    bl_idname = "scene.amaranth_lighters_corner_refresh"
    bl_label = "Refresh"
    bl_description = ("Generate/Refresh the Lists\n"
                      "Use to generate/refresh the list or after changes to Data")
    bl_options = {"REGISTER", "INTERNAL"}

    what: StringProperty(default="NONE")

    def execute(self, context):
        message = "No changes applied"

        if self.what == "LIGHTS":
            fill_ligters_corner_props(context, refresh=True)

            found_lights = len(context.window_manager.amth_lighters_state.keys())
            message = "No Lights in the Data" if found_lights == 0 else \
                    "Generated list for {} found light(s)".format(found_lights)

        elif self.what == "IMAGES":
            fill_missing_images_props(context, refresh=True)

            found_images = len(context.window_manager.amth_missing_images_state.keys())
            message = "Great! No missing Images" if found_images == 0 else \
                    "Missing {} image(s) in the Data".format(found_images)

        self.report({'INFO'}, message)

        return {"FINISHED"}


class AMTH_SCENE_PT_scene_debug(Panel):
    """Scene Debug"""
    bl_label = "Scene Debug"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="RADIOBUT_ON")

    def draw_label(self, layout, body_text, single, multi, lists, ico="BLANK1"):
        layout.label(
            text="{} {} {}".format(
                str(len(lists)), body_text,
                single if len(lists) == 1 else multi),
            icon=ico
            )

    def draw_miss_link(self, layout, text1, single, multi, text2, count, ico="BLANK1"):
        layout.label(
            text="{} {} {} {}".format(
                count, text1,
                single if count == 1 else multi, text2),
            icon=ico
            )

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        has_images = len(bpy.data.images)
        engine = scene.render.engine

        # List Missing Images
        box = layout.box()
        split = box.split(factor=0.8, align=True)
        row = split.row()

        if has_images:
            subrow = split.row(align=True)
            subrow.alignment = "RIGHT"
            subrow.operator(AMTH_SCENE_OT_Collection_List_Refresh.bl_idname,
                        text="", icon="FILE_REFRESH").what = "IMAGES"
            image_state = context.window_manager.amth_missing_images_state

            row.label(
                text="{} Image Blocks present in the Data".format(has_images),
                icon="IMAGE_DATA"
                )
            if len(image_state.keys()) > 0:
                box.template_list(
                        'AMTH_UL_MissingImages_UI',
                        'amth_collection_index_prop',
                        context.window_manager,
                        'amth_missing_images_state',
                        context.window_manager.amth_collection_index_prop,
                        'index_image',
                        rows=3
                        )
        else:
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
            if len(AMTH_store_data.mat_shaders) != 0:
                row.operator(
                    AMTH_SCENE_OT_list_users_debug_clear.bl_idname,
                    icon="X", text="").what = "SHADER"
            col.separator()

            if len(AMTH_store_data.mat_shaders) != 0:
                col = box.column(align=True)
                self.draw_label(col, "found", "material", "materials",
                        AMTH_store_data.mat_shaders, "INFO"
                        )
                for i, mat in enumerate(AMTH_store_data.mat_shaders):
                    col.label(
                        text="{}".format(AMTH_store_data.mat_shaders[i]), icon="MATERIAL"
                        )

        # List Missing Node Trees
        box = layout.box()
        row = box.row(align=True)
        split = row.split()
        col = split.column(align=True)

        split = col.split(align=True)
        split.label(text="Node Links")
        row = split.row(align=True)
        row.operator(AMTH_SCENE_OT_list_missing_node_links.bl_idname,
                       icon="NODETREE")

        if AMTH_store_data.count_groups != 0 or \
                AMTH_store_data.count_images != 0 or \
                AMTH_store_data.count_image_node_unlinked != 0:

            row.operator(
                AMTH_SCENE_OT_list_users_debug_clear.bl_idname,
                icon="X", text="").what = "NODE_LINK"
            col.label(text="Warning! Check Console", icon="ERROR")

        if AMTH_store_data.count_groups != 0:
            self.draw_miss_link(col, "node", "group", "groups", "missing link",
                    AMTH_store_data.count_groups, "NODE_TREE"
                    )
        if AMTH_store_data.count_images != 0:
            self.draw_miss_link(col, "image", "node", "nodes", "missing link",
                    AMTH_store_data.count_images, "IMAGE_DATA"
                    )
        if AMTH_store_data.count_image_node_unlinked != 0:
            self.draw_miss_link(col, "image", "node", "nodes", "with no output connected",
                    AMTH_store_data.count_image_node_unlinked, "NODE"
                    )

        # List Empty Materials Slots
        box = layout.box()
        split = box.split()
        col = split.column(align=True)
        col.label(text="Material Slots")

        row = split.row(align=True)
        row.operator(AMTH_SCENE_OT_list_missing_material_slots.bl_idname,
                    icon="MATERIAL",
                    text="List Empty Materials Slots"
                    )
        if len(AMTH_store_data.obj_mat_slots) != 0:
            row.operator(
                AMTH_SCENE_OT_list_users_debug_clear.bl_idname,
                icon="X", text="").what = "MAT_SLOTS"

            col.separator()
            col = box.column(align=True)
            self.draw_label(col, "found empty material slot", "object", "objects",
                    AMTH_store_data.obj_mat_slots, "INFO"
                    )
        for entry, obs in enumerate(AMTH_store_data.obj_mat_slots):
            row = col.row()
            row.alignment = "LEFT"
            row.label(
                text="{}".format(AMTH_store_data.obj_mat_slots[entry]),
                icon="OBJECT_DATA")

        if AMTH_store_data.obj_mat_slots_lib:
            col.separator()
            col.label("Check {}:".format(
                "this library" if
                len(AMTH_store_data.obj_mat_slots_lib) == 1 else
                "these libraries")
                )
            for ilib, libs in enumerate(AMTH_store_data.obj_mat_slots_lib):
                row = col.row(align=True)
                row.alignment = "LEFT"
                row.operator(
                    AMTH_SCENE_OT_blender_instance_open.bl_idname,
                    text=AMTH_store_data.obj_mat_slots_lib[ilib],
                    icon="LINK_BLEND",
                    emboss=False).filepath = AMTH_store_data.obj_mat_slots_lib[ilib]

        box = layout.box()
        row = box.row(align=True)
        row.label(text="List Users for Datablock")

        col = box.column(align=True)
        split = col.split()
        row = split.row(align=True)
        row.prop(
                scene, "amth_datablock_types",
                icon=scene.amth_datablock_types,
                text=""
                )
        row.operator_menu_enum(
                "scene.amth_list_users_for_x_type",
                "list_type_select",
                text=scene.amth_list_users_for_x_name
                )

        row = split.row(align=True)
        row.enabled = True if USER_X_NAME_EMPTY not in scene.amth_list_users_for_x_name else False
        row.operator(
                AMTH_SCENE_OT_list_users_for_x.bl_idname,
                icon="COLLAPSEMENU").name = scene.amth_list_users_for_x_name

        if any(val for val in AMTH_store_data.users.values()):
            col = box.column(align=True)

            for t in AMTH_store_data.users:

                for ma in AMTH_store_data.users[t]:
                    subrow = col.row(align=True)
                    subrow.alignment = "LEFT"

                    if t == 'OBJECT_DATA':
                        text_lib = " [L] " if \
                                ma in bpy.data.objects and bpy.data.objects[ma].library else ""
                        subrow.operator(
                            AMTH_SCENE_OT_amaranth_object_select.bl_idname,
                            text="{} {}{}".format(text_lib, ma,
                             "" if ma in context.scene.objects else " [Not in Scene]"),
                            icon=t,
                            emboss=False).object_name = ma
                    else:
                        subrow.label(text=ma, icon=t)
            row.operator(
            AMTH_SCENE_OT_list_users_debug_clear.bl_idname,
            icon="X", text="").what = "XTYPE"

        if AMTH_store_data.libraries:
            count_lib = 0

            col.separator()
            col.label("Check {}:".format(
                "this library" if
                len(AMTH_store_data.libraries) == 1 else
                "these libraries")
                )
            for libs in AMTH_store_data.libraries:
                count_lib += 1
                row = col.row(align=True)
                row.alignment = "LEFT"
                row.operator(
                    AMTH_SCENE_OT_blender_instance_open.bl_idname,
                    text=AMTH_store_data.libraries[count_lib - 1],
                    icon="LINK_BLEND",
                    emboss=False).filepath = AMTH_store_data.libraries[count_lib - 1]


class AMTH_PT_LightersCorner(Panel):
    """The Lighters Panel"""
    bl_label = "Lighter's Corner"
    bl_idname = "AMTH_SCENE_PT_lighters_corner"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="LIGHT_SUN")

    def draw(self, context):
        layout = self.layout
        state_props = len(context.window_manager.amth_lighters_state)
        engine = context.scene.render.engine
        box = layout.box()
        row = box.row(align=True)

        if utils.cycles_exists():
            row.prop(context.scene, "amaranth_lighterscorner_list_meshlights")

        subrow = row.row(align=True)
        subrow.alignment = "RIGHT"
        subrow.operator(AMTH_SCENE_OT_Collection_List_Refresh.bl_idname,
                text="", icon="FILE_REFRESH").what = "LIGHTS"

        if not state_props:
            row = box.row()
            message = "Please Refresh" if len(bpy.data.lights) > 0 else "No Lights in Data"
            row.label(text=message, icon="INFO")
        else:
            row = box.row(align=True)
            split = row.split(factor=0.5, align=True)
            col = split.column(align=True)

            col.label(text="Name/Library link")

            if engine in ["CYCLES"]:
                splits = 0.4
                splita = split.split(factor=splits, align=True)

                if utils.cycles_exists() and engine == "CYCLES":
                    col = splita.column(align=True)
                    col.label(text="Size")

            cols = row.row(align=True)
            cols.alignment = "RIGHT"
            cols.label(text="{}Render Visibility/Selection".format(
                  "Rays /" if utils.cycles_exists() else "")
                )
            box.template_list(
                    'AMTH_UL_LightersCorner_UI',
                    'amth_collection_index_prop',
                    context.window_manager,
                    'amth_lighters_state',
                    context.window_manager.amth_collection_index_prop,
                    'index',
                    rows=5
                    )


class AMTH_UL_MissingImages_UI(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        text_lib = item.text_lib
        has_filepath = item.has_filepath
        is_library = item.is_library

        split = layout.split(factor=0.4)
        row = split.row(align=True)
        row.alignment = "LEFT"
        row.label(text=text_lib, icon="IMAGE_DATA")
        image = bpy.data.images.get(item.name, None)

        subrow = split.row(align=True)
        splitp = subrow.split(factor=0.8, align=True).row(align=True)
        splitp.alignment = "LEFT"
        row_lib = subrow.row(align=True)
        row_lib.alignment = "RIGHT"
        if not image:
            splitp.label(text="Image is not available", icon="ERROR")
        else:
            splitp.label(text=has_filepath, icon="LIBRARY_DATA_DIRECT")
            if is_library:
                row_lib.operator(
                    AMTH_SCENE_OT_blender_instance_open.bl_idname,
                    text="",
                    emboss=False, icon="LINK_BLEND").filepath = is_library


class AMTH_UL_LightersCorner_UI(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        icon_type = item.icon_type
        engine = context.scene.render.engine
        text_lib = item.text_lib
        is_library = item.is_library

        split = layout.split(factor=0.35)
        row = split.row(align=True)
        row.alignment = "LEFT"
        row.label(text=text_lib, icon=icon_type)
        ob = bpy.data.objects.get(item.name, None)
        if not ob:
            row.label(text="Object is not available", icon="ERROR")
        else:
            if is_library:
                row.operator(
                    AMTH_SCENE_OT_blender_instance_open.bl_idname,
                    text="",
                    emboss=False, icon="LINK_BLEND").filepath = is_library

            rows = split.row(align=True)
            splits = 0.4
            splitlamp = rows.split(factor=splits, align=True)
            splitlampc = splitlamp.row(align=True)
            splitlampd = rows.row(align=True)
            splitlampd.alignment = "RIGHT"

            if utils.cycles_exists() and engine == "CYCLES":
                if "LIGHT" in icon_type:
                    clamp = ob.data.cycles
                    lamp = ob.data
                    if lamp.type in ["POINT", "SUN", "SPOT"]:
                        splitlampc.label(text="{:.2f}".format(lamp.shadow_soft_size))
                    elif lamp.type == "HEMI":
                        splitlampc.label(text="N/A")
                    elif lamp.type == "AREA" and lamp.shape == "RECTANGLE":
                        splitlampc.label(
                            text="{:.2f} x {:.2f}".format(lamp.size, lamp.size_y)
                            )
                    else:
                        splitlampc.label(text="{:.2f}".format(lamp.size))
            if utils.cycles_exists():
                splitlampd.prop(ob, "visible_camera", text="")
                splitlampd.prop(ob, "visible_diffuse", text="")
                splitlampd.prop(ob, "visible_glossy", text="")
                splitlampd.prop(ob, "visible_shadow", text="")
                splitlampd.separator()
            splitlampd.prop(ob, "hide_viewport", text="", emboss=False)
            splitlampd.prop(ob, "hide_render", text="", emboss=False)
            splitlampd.operator(
                    AMTH_SCENE_OT_amaranth_object_select.bl_idname,
                    text="",
                    emboss=False, icon="RESTRICT_SELECT_OFF").object_name = item.name


def fill_missing_images_props(context, refresh=False):
    image_state = context.window_manager.amth_missing_images_state
    if refresh:
        for key in image_state.keys():
            index = image_state.find(key)
            if index != -1:
                image_state.remove(index)

    for im in bpy.data.images:
        if im.type not in ("UV_TEST", "RENDER_RESULT", "COMPOSITING"):
            if not im.packed_file and \
                    not os.path.exists(bpy.path.abspath(im.filepath, library=im.library)):
                text_l = "{}{} [{}]{}".format("[L] " if im.library else "", im.name,
                    im.users, " [F]" if im.use_fake_user else "")
                prop = image_state.add()
                prop.name = im.name
                prop.text_lib = text_l
                prop.has_filepath = im.filepath if im.filepath else "No Filepath"
                prop.is_library = im.library.filepath if im.library else ""


def fill_ligters_corner_props(context, refresh=False):
    light_state = context.window_manager.amth_lighters_state
    list_meshlights = context.scene.amaranth_lighterscorner_list_meshlights
    if refresh:
        for key in light_state.keys():
            index = light_state.find(key)
            if index != -1:
                light_state.remove(index)

    for ob in bpy.data.objects:
        if ob.name not in light_state.keys() or refresh:
            is_light = ob.type == "LIGHT"
            is_emission = True if utils.cycles_is_emission(
                    context, ob) and list_meshlights else False

            if is_light or is_emission:
                icons = "LIGHT_%s" % ob.data.type if is_light else "MESH_GRID"
                text_l = "{} {}{}".format(" [L] " if ob.library else "", ob.name,
                        "" if ob.name in context.scene.objects else " [Not in Scene]")
                prop = light_state.add()
                prop.name = ob.name
                prop.icon_type = icons
                prop.text_lib = text_l
                prop.is_library = ob.library.filepath if ob.library else ""


class AMTH_LightersCornerStateProp(PropertyGroup):
    icon_type: StringProperty()
    text_lib: StringProperty()
    is_library: StringProperty()


class AMTH_MissingImagesStateProp(PropertyGroup):
    text_lib: StringProperty()
    has_filepath: StringProperty()
    is_library: StringProperty()


class AMTH_LightersCollectionIndexProp(PropertyGroup):
    index: IntProperty(
            name="index"
            )
    index_image: IntProperty(
            name="index"
            )


classes = (
    AMTH_SCENE_PT_scene_debug,
    AMTH_SCENE_OT_list_users_debug_clear,
    AMTH_SCENE_OT_blender_instance_open,
    AMTH_SCENE_OT_amaranth_object_select,
    AMTH_SCENE_OT_list_missing_node_links,
    AMTH_SCENE_OT_list_missing_material_slots,
    AMTH_SCENE_OT_cycles_shader_list_nodes,
    AMTH_SCENE_OT_list_users_for_x,
    AMTH_SCENE_OT_list_users_for_x_type,
    AMTH_SCENE_OT_Collection_List_Refresh,
    AMTH_LightersCornerStateProp,
    AMTH_LightersCollectionIndexProp,
    AMTH_MissingImagesStateProp,
    AMTH_PT_LightersCorner,
    AMTH_UL_LightersCorner_UI,
    AMTH_UL_MissingImages_UI,
)


def register():
    init()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.amth_list_users_for_x_name = StringProperty(
            default="Select DataBlock Name",
            name="Name",
            description=USER_X_NAME_EMPTY,
            options={"SKIP_SAVE"}
            )
    bpy.types.WindowManager.amth_collection_index_prop = PointerProperty(
            type=AMTH_LightersCollectionIndexProp
            )
    bpy.types.WindowManager.amth_lighters_state = CollectionProperty(
            type=AMTH_LightersCornerStateProp
            )
    bpy.types.WindowManager.amth_missing_images_state = CollectionProperty(
            type=AMTH_MissingImagesStateProp
            )


def unregister():
    clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.amth_list_users_for_x_name
    del bpy.types.WindowManager.amth_collection_index_prop
    del bpy.types.WindowManager.amth_lighters_state
    del bpy.types.WindowManager.amth_missing_images_state
