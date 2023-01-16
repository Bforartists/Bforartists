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

bl_info = {
    "name": "Export: Adobe After Effects (.jsx)",
    "description": "Export cameras, selected objects & camera solution "
        "3D Markers to Adobe After Effects CS3 and above",
    "author": "Bartek Skorupa, Damien Picard (@pioverfour)",
    "version": (0, 1, 3),
    "blender": (2, 80, 0),
    "location": "File > Export > Adobe After Effects (.jsx)",
    "warning": "",
    "doc_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
               "Scripts/Import-Export/Adobe_After_Effects",
    "category": "Import-Export",
}


import bpy
import os
import datetime
from math import degrees
from mathutils import Matrix, Vector, Color


def get_camera_frame_ranges(scene, start, end):
    """Get frame ranges for each marker in the timeline

    For this, start at the end of the timeline,
    iterate through each camera-bound marker in reverse,
    and get the range from this marker to the end of the previous range.
    """
    markers = sorted((m for m in scene.timeline_markers if m.camera is not None),
                     key=lambda m:m.frame, reverse=True)

    if len(markers) <= 1:
        return [[[start, end], scene.camera],]

    camera_frame_ranges = []
    current_frame = end
    for m in markers:
        if m.frame < current_frame:
            camera_frame_ranges.append([[m.frame, current_frame + 1], m.camera])
            current_frame = m.frame - 1
    camera_frame_ranges.reverse()
    camera_frame_ranges[0][0][0] = start
    return camera_frame_ranges


class ObjectExport():
    """Base exporter class

    Collects data about an object and outputs the proper JSX script for AE.
    """
    def __init__(self, obj):
        self.obj = obj
        self.name_ae = convert_name(self.obj.name)
        self.keyframes = {}

    def get_prop_keyframe(self, prop_name, value, time):
        """Get keyframe for given property, only if different from previous value"""
        prop_keys = self.keyframes.setdefault(prop_name, [])
        if len(prop_keys) == 0:
            prop_keys.append([time, value, False])
            return

        if value != prop_keys[-1][1]:
            prop_keys.append([time, value, False])
        # Store which keys should hold, that is, which are
        # the first in a series of identical values
        else:
            prop_keys[-1][2] = True

    def get_keyframe(self, context, width, height, aspect, time, ae_size):
        """Store animation for the current frame"""
        ae_transform = convert_transform_matrix(self.obj.matrix_world,
                                                width, height, aspect, ae_size)

        self.get_prop_keyframe('position', ae_transform[0:3], time)
        self.get_prop_keyframe('orientation', ae_transform[3:6], time)
        self.get_prop_keyframe('scale', ae_transform[6:9], time)

    def get_obj_script(self, include_animation):
        """Get the JSX script for the object"""
        return self.get_type_script() + self.get_anim_script(include_animation) + self.get_post_script()

    def get_type_script(self):
        """Get the basic part of the JSX script"""
        type_script = f'var {self.name_ae} = newComp.layers.addNull();\n'
        type_script += f'{self.name_ae}.threeDLayer = true;\n'
        type_script += f'{self.name_ae}.source.name = "{self.name_ae}";\n'
        return type_script

    def get_anim_script(self, include_animation):
        """Get the part of the JSX script encoding animation"""
        anim_script = ""

        # Set values of properties, add keyframes only where needed
        for prop, keys in self.keyframes.items():
            if include_animation and len(keys) > 1:
                times = ",".join(str(k[0]) for k in keys)
                values = ",".join(str(k[1]) for k in keys).replace(" ", "")
                anim_script += (
                    f'{self.name_ae}.property("{prop}").setValuesAtTimes([{times}],[{values}]);\n')

                # Set to HOLD the frames after which animation is fixed
                # for several frames, to avoid interpolation errors
                if any(k[2] for k in keys):
                    anim_script += (
                        f'var hold_frames = {[i + 1 for i, k in enumerate(keys) if k[2]]};\n'
                        'for (var i = 0; i < hold_frames.length; i++) {\n'
                        f'  {self.name_ae}.property("{prop}").setInterpolationTypeAtKey(hold_frames[i], KeyframeInterpolationType.HOLD);\n'
                        '}\n')

            # No animation for this property
            else:
                value = str(keys[0][1]).replace(" ", "")
                anim_script += (
                    f'{self.name_ae}.property("{prop}").setValue({value});\n')

        anim_script += '\n'

        return anim_script

    def get_post_script(self):
        """This is only used in lights as a post-treatment after animation"""
        return ""

class CameraExport(ObjectExport):
    def __init__(self, obj, start_time=None, end_time=None):
        super().__init__(obj)
        self.start_time = start_time
        self.end_time = end_time

    def get_keyframe(self, context, width, height, aspect, time, ae_size):
        ae_transform = convert_transform_matrix(self.obj.matrix_world,
                                                width, height, aspect, ae_size)
        zoom = convert_lens(self.obj, width, height,
                            aspect)

        self.get_prop_keyframe('position', ae_transform[0:3], time)
        self.get_prop_keyframe('orientation', ae_transform[3:6], time)
        self.get_prop_keyframe('zoom', zoom, time)

    def get_type_script(self):
        type_script = f'var {self.name_ae} = newComp.layers.addCamera("{self.name_ae}",[0,0]);\n'
        # Restrict time range when multiple cameras are used (markers)
        if self.start_time is not None:
            type_script += f'{self.name_ae}.inPoint = {self.start_time};\n'
            type_script += f'{self.name_ae}.outPoint = {self.end_time};\n'
        type_script += f'{self.name_ae}.autoOrient = AutoOrientType.NO_AUTO_ORIENT;\n'
        return type_script


class LightExport(ObjectExport):
    def get_keyframe(self, context, width, height, aspect, time, ae_size):
        ae_transform = convert_transform_matrix(self.obj.matrix_world,
                                                width, height, aspect, ae_size)
        self.type = self.obj.data.type
        color = list(self.obj.data.color)
        intensity = self.obj.data.energy * 10.0

        self.get_prop_keyframe('position', ae_transform[0:3], time)
        if self.type in {'SPOT', 'SUN'}:
            self.get_prop_keyframe('orientation', ae_transform[3:6], time)
        self.get_prop_keyframe('intensity', intensity, time)
        self.get_prop_keyframe('Color', color, time)
        if self.type == 'SPOT':
            cone_angle = degrees(self.obj.data.spot_size)
            self.get_prop_keyframe('Cone Angle', cone_angle, time)
            cone_feather = self.obj.data.spot_blend * 100.0
            self.get_prop_keyframe('Cone Feather', cone_feather, time)

    def get_type_script(self):
        type_script = f'var {self.name_ae} = newComp.layers.addLight("{self.name_ae}", [0.0, 0.0]);\n'
        type_script += f'{self.name_ae}.autoOrient = AutoOrientType.NO_AUTO_ORIENT;\n'
        type_script += f'{self.name_ae}.lightType = LightType.SPOT;\n'
        return type_script

    def get_post_script(self):
        """Set light type _after_ the orientation, otherwise the property is hidden in AE..."""
        if self.obj.data.type == 'SUN':
            post_script = f'{self.name_ae}.lightType = LightType.PARALLEL;\n'
        elif self.obj.data.type == 'SPOT':
            post_script = f'{self.name_ae}.lightType = LightType.SPOT;\n'
        else:
            post_script = f'{self.name_ae}.lightType = LightType.POINT;\n'
        return post_script


class ImageExport(ObjectExport):
    def get_keyframe(self, context, width, height, aspect, time, ae_size):
        # Convert obj transform properties to AE space
        plane_matrix = get_image_plane_matrix(self.obj)
        # Scale plane to account for AE's transforms
        plane_matrix = plane_matrix @ Matrix.Scale(100.0 / width, 4)

        ae_transform = convert_transform_matrix(plane_matrix,
                                                width, height, aspect, ae_size)
        opacity = 0.0 if self.obj.hide_render else 100.0

        if not hasattr(self, 'filepath'):
            self.filepath = get_image_filepath(self.obj)

        image_width, image_height = get_image_size(self.obj)
        ratio_to_comp = image_width / width
        scale = ae_transform[6:9]
        if image_height != 0.0:
            scale[1] *= image_width / image_height
        if ratio_to_comp != 0.0:
            scale[0] /= ratio_to_comp
            scale[1] /= ratio_to_comp

        self.get_prop_keyframe('position', ae_transform[0:3], time)
        self.get_prop_keyframe('orientation', ae_transform[3:6], time)
        self.get_prop_keyframe('scale', scale, time)
        self.get_prop_keyframe('opacity', opacity, time)

    def get_type_script(self):
        type_script = f'var newFootage = app.project.importFile(new ImportOptions(File("{self.filepath}")));\n'
        type_script += 'newFootage.parentFolder = footageFolder;\n'
        type_script += f'var {self.name_ae} = newComp.layers.add(newFootage);\n'
        type_script += f'{self.name_ae}.threeDLayer = true;\n'
        type_script += f'{self.name_ae}.source.name = "{self.name_ae}";\n'
        return type_script


class SolidExport(ObjectExport):
    def get_keyframe(self, context, width, height, aspect, time, ae_size):
        # Convert obj transform properties to AE space
        plane_matrix = get_plane_matrix(self.obj)
        # Scale plane to account for AE's transforms
        plane_matrix = plane_matrix @ Matrix.Scale(100.0 / width, 4)

        ae_transform = convert_transform_matrix(plane_matrix,
                                                width, height, aspect, ae_size)
        opacity = 0.0 if self.obj.hide_render else 100.0

        if not hasattr(self, 'color'):
            self.color = get_plane_color(self.obj)
        if not hasattr(self, 'width'):
            self.width = width
        if not hasattr(self, 'height'):
            self.height = height

        scale = ae_transform[6:9]
        scale[1] *= width / height

        self.get_prop_keyframe('position', ae_transform[0:3], time)
        self.get_prop_keyframe('orientation', ae_transform[3:6], time)
        self.get_prop_keyframe('scale', scale, time)
        self.get_prop_keyframe('opacity', opacity, time)

    def get_type_script(self):
        type_script = f'var {self.name_ae} = newComp.layers.addSolid({self.color},"{self.name_ae}",{self.width},{self.height},1.0);\n'
        type_script += f'{self.name_ae}.source.name = "{self.name_ae}";\n'
        type_script += f'{self.name_ae}.source.parentFolder = footageFolder;\n'
        type_script += f'{self.name_ae}.threeDLayer = true;\n'
        return type_script


class CamBundleExport(ObjectExport):
    def __init__(self, obj, track):
        self.obj = obj
        self.track = track
        self.name_ae = convert_name(f'{obj.name}__{track.name}')
        self.keyframes = {}

    def get_keyframe(self, context, width, height, aspect, time, ae_size):
        # Bundles are in camera space.
        # Transpose to world space
        matrix = self.obj.matrix_basis @ Matrix.Translation(self.track.bundle)
        # Convert the position into AE space
        ae_transform = convert_transform_matrix(matrix,
                                                width, height, aspect, ae_size)

        self.get_prop_keyframe('position', ae_transform[0:3], time)
        self.get_prop_keyframe('orientation', ae_transform[3:6], time)

    def get_type_script(self):
        type_script = f'var {self.name_ae} = newComp.layers.addNull();\n'
        type_script += f'{self.name_ae}.threeDLayer = true;\n'
        type_script += f'{self.name_ae}.source.name = "{self.name_ae}";\n'
        return type_script


def get_camera_bundles(scene, camera):
    cam_bundles = []

    for constraint in camera.constraints:
        if constraint.type == 'CAMERA_SOLVER':
            # Which movie clip does it use
            if constraint.use_active_clip:
                clip = scene.active_clip
            else:
                clip = constraint.clip

            # Go through each tracking point
            for track in clip.tracking.tracks:
                # Does this tracking point have a bundle
                # (has its 3D position been solved)
                if track.has_bundle:
                    cam_bundles.append(CamBundleExport(camera, track))

    return cam_bundles


def get_selected(context, include_active_cam, include_selected_cams,
                 include_selected_objects, include_cam_bundles,
                 include_image_planes, include_solids):
    """Create manageable list of selected objects"""
    cameras = []
    solids = []       # Meshes exported as AE solids
    images = []       # Meshes exported as AE AV layers
    lights = []       # Lights exported as AE lights
    cam_bundles = []  # Camera trackers exported as AE nulls
    nulls = []        # Remaining objects exported as AE nulls

    scene = context.scene
    fps = scene.render.fps / scene.render.fps_base

    if context.scene.camera is not None:
        if include_active_cam:
            for frame_range, camera in get_camera_frame_ranges(
                    context.scene,
                    context.scene.frame_start, context.scene.frame_end):

                if (include_cam_bundles
                        and camera not in (cam.obj for cam in cameras)):
                    cam_bundles.extend(
                        get_camera_bundles(context.scene, camera))

                cameras.append(
                    CameraExport(camera,
                                 (frame_range[0] - scene.frame_start) / fps,
                                 (frame_range[1] - scene.frame_start) / fps))

    for obj in context.selected_objects:
        if obj.type == 'CAMERA':
            # Ignore camera if already selected
            if obj in (cam.obj for cam in cameras):
                continue
            if include_selected_cams:
                cameras.append(CameraExport(obj))
            if include_cam_bundles:
                cam_bundles.extend(get_camera_bundles(context.scene, obj))

        elif include_image_planes and is_image_plane(obj):
            images.append(ImageExport(obj))

        elif include_solids and is_plane(obj):
            solids.append(SolidExport(obj))

        elif include_selected_objects:
            if obj.type == 'LIGHT':
                lights.append(LightExport(obj))
            else:
                nulls.append(ObjectExport(obj))

    return {'cameras': cameras,
            'images': images,
            'solids': solids,
            'lights': lights,
            'nulls': nulls,
            'cam_bundles': cam_bundles}


def get_first_material(obj):
    for slot in obj.material_slots:
        if slot.material is not None:
            return slot.material


def get_image_node(mat):
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            return node.image


def get_plane_color(obj):
    """Get the object's emission and base color, or 0.5 gray if no color is found."""
    if obj.active_material is None:
        color = (0.5,) * 3
    elif obj.active_material:
        from bpy_extras import node_shader_utils
        wrapper = node_shader_utils.PrincipledBSDFWrapper(obj.active_material)
        color = Color(wrapper.base_color[:3]) + wrapper.emission_color

    return str(list(color))


def is_plane(obj):
    """Check if object is a plane

    Makes a few assumptions:
    - The mesh has exactly one quad face
    - The mesh is a rectangle

    For now this doesn't account for shear, which could happen e.g. if the
    vertices are rotated, and the object is scaled non-uniformly...
    """
    if obj.type != 'MESH':
        return False

    if len(obj.data.polygons) != 1:
        return False

    if len(obj.data.polygons[0].vertices) != 4:
        return False

    v1, v2, v3, v4 = (obj.data.vertices[v].co for v in obj.data.polygons[0].vertices)

    # Check that poly is a parallelogram
    if -v1 + v2 + v4 != v3:
        return False

    # Check that poly has at least one right angle
    if (v2-v1).dot(v4-v1) != 0.0:
        return False

    # If my calculations are correct, that should make it a rectangle
    return True


def is_image_plane(obj):
    """Check if object is a plane with an image

    Makes a few assumptions:
    - The mesh is a plane
    - The mesh has exactly one material
    - There is only one image in this material node tree
    - The rectangle is UV unwrapped and its UV is occupying the whole space
    """
    if not is_plane(obj):
        return False

    if len(obj.material_slots) == 0:
        return False

    mat = get_first_material(obj)
    if mat is None:
        return False

    img = get_image_node(mat)
    if img is None:
        return False

    if len(obj.data.vertices) != 4:
        return False

    if not get_image_plane_matrix(obj):
        return False

    return True

def get_image_filepath(obj):
    mat = get_first_material(obj)
    img = get_image_node(mat)
    filepath = img.filepath
    filepath = bpy.path.abspath(filepath)
    filepath = os.path.abspath(filepath)
    filepath = filepath.replace('\\', '\\\\')
    return filepath


def get_image_size(obj):
    mat = get_first_material(obj)
    img = get_image_node(mat)
    return img.size


def get_plane_matrix(obj):
    """Get object's polygon local matrix from vertices."""
    v1, v2, v3, v4 = (obj.data.vertices[v].co for v in obj.data.polygons[0].vertices)

    p0 = obj.matrix_world @ v1
    px = obj.matrix_world @ v2 - p0
    py = obj.matrix_world @ v4 - p0

    rot_mat = Matrix((px, py, px.cross(py))).transposed().to_4x4()
    trans_mat = Matrix.Translation(p0 + (px + py) / 2.0)
    mat = trans_mat @ rot_mat

    return mat


def get_image_plane_matrix(obj):
    """Get object's polygon local matrix from uvs.

    This will only work if uvs occupy all space, to get bounds
    """
    p0, px, py = None, None, None
    for p_i, p in enumerate(obj.data.uv_layers.active.data):
        if p.uv == Vector((0, 0)):
            p0 = p_i
        elif p.uv == Vector((1, 0)):
            px = p_i
        elif p.uv == Vector((0, 1)):
            py = p_i

    if None in (p0, px, py):
        return False

    verts = obj.data.vertices
    loops = obj.data.loops

    p0 = obj.matrix_world @ verts[loops[p0].vertex_index].co
    px = obj.matrix_world @ verts[loops[px].vertex_index].co - p0
    py = obj.matrix_world @ verts[loops[py].vertex_index].co - p0

    rot_mat = Matrix((px, py, px.cross(py))).transposed().to_4x4()
    trans_mat = Matrix.Translation(p0 + (px + py) / 2.0)
    mat = trans_mat @ rot_mat

    return mat


def convert_name(name):
    """Convert names of objects to avoid errors in AE"""
    if not name[0].isalpha():
        name = "_" + name
    name = bpy.path.clean_name(name)
    name = name.replace("-", "_")

    return name


def convert_transform_matrix(matrix, width, height, aspect, ae_size=100.0):
    """Convert from Blender's Location, Rotation and Scale
    to AE's Position, Rotation/Orientation and Scale

    This function will be called for every object for every frame
    """

    # Get blender transform data for object
    b_loc = matrix.to_translation()
    b_rot = matrix.to_euler('ZYX')  # ZYX euler matches AE's orientation and allows to use x_rot_correction
    b_scale = matrix.to_scale()

    # Convert to AE Position Rotation and Scale. Axes in AE are different:
    # AE's X is Blender's X,
    # AE's Y is Blender's -Z,
    # AE's Z is Blender's Y
    x = (b_loc.x * 100.0 / aspect + width / 2.0) * ae_size / 100.0
    y = (-b_loc.z * 100.0 + height / 2.0) * ae_size / 100.0
    z = (b_loc.y * 100.0) * ae_size / 100.0

    # Convert rotations to match AE's orientation.
    # In Blender, object of zero rotation lays on floor.
    # In AE, layer of zero orientation "stands", so subtract 90 degrees
    rx =  degrees(b_rot.x) - 90.0  # AE's X orientation =  blender's X rotation if 'ZYX' euler.
    ry = -degrees(b_rot.y)  # AE's Y orientation = -blender's Y rotation if 'ZYX' euler
    rz = -degrees(b_rot.z)  # AE's Z orientation = -blender's Z rotation if 'ZYX' euler

    # Convert scale to AE scale. ae_size is a global multiplier.
    sx = b_scale.x * ae_size
    sy = b_scale.y * ae_size
    sz = b_scale.z * ae_size

    return [x, y, z, rx, ry, rz, sx, sy, sz]


# Get camera's lens and convert to AE's "zoom" value in pixels
# this function will be called for every camera for every frame
#
#
# AE's lens is defined by "zoom" in pixels.
# Zoom determines focal angle or focal length.
#
# ZOOM VALUE CALCULATIONS:
#
# Given values:
#     - sensor width (camera.data.sensor_width)
#     - sensor height (camera.data.sensor_height)
#     - sensor fit (camera.data.sensor_fit)
#     - lens (blender's lens in mm)
#     - width (width of the composition/scene in pixels)
#     - height (height of the composition/scene in pixels)
#     - PAR (pixel aspect ratio)
#
# Calculations are made using sensor's size and scene/comp dimension (width or height).
# If camera.sensor_fit is set to 'HORIZONTAL':
#     sensor = camera.data.sensor_width, dimension = width.
#
# If camera.sensor_fit is set to 'AUTO':
#     sensor = camera.data.sensor_width
# (actually, it just means to use the first value)
# In AUTO, if the vertical size is greater than the horizontal size:
#     dimension = width
# else:
#     dimension = height
#
# If camera.sensor_fit is set to 'VERTICAL':
#    sensor = camera.data.sensor_height, dimension = height
#
# Zoom can be calculated using simple proportions.
#
#                             |
#                           / |
#                         /   |
#                       /     | d
#       s  |\         /       | i
#       e  |  \     /         | m
#       n  |    \ /           | e
#       s  |    / \           | n
#       o  |  /     \         | s
#       r  |/         \       | i
#                       \     | o
#          |     |        \   | n
#          |     |          \ |
#          |     |            |
#           lens |    zoom
#
#     zoom / dimension = lens / sensor   =>
#     zoom = lens * dimension / sensor
#
# Above is true if square pixels are used. If not,
# aspect compensation is needed, so final formula is:
#     zoom = lens * dimension / sensor * aspect

def convert_lens(camera, width, height, aspect):
    if camera.data.sensor_fit == 'VERTICAL':
        sensor = camera.data.sensor_height
    else:
        sensor = camera.data.sensor_width

    if (camera.data.sensor_fit == 'VERTICAL'
            or camera.data.sensor_fit == 'AUTO'
            and (width / height) * aspect < 1.0):
        dimension = height
    else:
        dimension = width

    zoom = camera.data.lens * dimension / sensor * aspect

    return zoom

# convert object bundle's matrix. Not ready yet. Temporarily not active
# def get_ob_bundle_matrix_world(cam_matrix_world, bundle_matrix):
#    matrix = cam_matrix_basis
#    return matrix


def write_jsx_file(context, file, selection, include_animation, ae_size):
    """jsx script for AE creation"""

    print("\n---------------------------\n"
          "- Export to After Effects -\n"
          "---------------------------")

    # Create list of static blender data
    scene = context.scene
    width = scene.render.resolution_x
    height = scene.render.resolution_y
    aspect_x = scene.render.pixel_aspect_x
    aspect_y = scene.render.pixel_aspect_y
    aspect = aspect_x / aspect_y
    if include_animation:
        frame_end = scene.frame_end + 1
    else:
        frame_end = scene.frame_start + 1
    fps = scene.render.fps / scene.render.fps_base
    duration = (frame_end - scene.frame_start) / fps

    # Store the current frame to restore it at the end of export
    frame_current = scene.frame_current

    # Get all keyframes for each object
    for frame in range(scene.frame_start, frame_end):
        print("Working on frame: " + str(frame))
        scene.frame_set(frame)

        # Get time for this loop
        time = (frame - scene.frame_start) / fps

        for obj_type in selection.values():
            for obj in obj_type:
                obj.get_keyframe(context, width, height, aspect, time, ae_size)

    # ---- write JSX file
    with open(file, 'w') as jsx_file:
        # Make the jsx executable in After Effects (enable double click on jsx)
        jsx_file.write('#target AfterEffects\n\n')
        # Script's header
        jsx_file.write('/**************************************\n')
        jsx_file.write(f'Scene : {scene.name}\n')
        jsx_file.write(f'Resolution : {width} x {height}\n')
        jsx_file.write(f'Duration : {duration}\n')
        jsx_file.write(f'FPS : {fps}\n')
        jsx_file.write(f'Date : {datetime.datetime.now()}\n')
        jsx_file.write('Exported with io_export_after_effects.py\n')
        jsx_file.write('**************************************/\n\n\n\n')

        # Wrap in function
        jsx_file.write("function compFromBlender(){\n")

        # Create new comp
        if bpy.data.filepath:
            comp_name = convert_name(
                os.path.splitext(os.path.basename(bpy.data.filepath))[0])
        else:
            comp_name = "BlendComp"
        jsx_file.write(f'\nvar compName = prompt("Blender Comp\'s Name \\nEnter Name of newly created Composition","{comp_name}","Composition\'s Name");\n')
        jsx_file.write('if (compName){')
        # Continue only if comp name is given. If not - terminate
        jsx_file.write(
            f'\nvar newComp = app.project.items.addComp(compName, {width}, '
            f'{height}, {aspect}, {duration}, {fps});')
        jsx_file.write(f"\nnewComp.displayStartTime = {scene.frame_start / fps};\n\n")

        jsx_file.write('var footageFolder = app.project.items.addFolder(compName + "_layers")\n\n\n')

        # Write each object's creation script
        for obj_type in ('cam_bundles', 'nulls', 'solids', 'images', 'lights', 'cameras'):
            if len(selection[obj_type]):
                type_name = 'CAMERA 3D MARKERS' if obj_type == 'cam_bundles' else obj_type.upper()
                jsx_file.write(f'// **************  {type_name}  **************\n\n')
                for obj in selection[obj_type]:
                    jsx_file.write(obj.get_obj_script(include_animation))
                jsx_file.write('\n')

        # Exit import if no comp name given
        jsx_file.write('\n}else{alert ("Exit Import Blender animation data \\nNo Comp name has been chosen","EXIT")};')
        # Close function
        jsx_file.write("}\n\n\n")
        # Execute function. Wrap in "undo group" for easy undoing import process
        jsx_file.write('app.beginUndoGroup("Import Blender animation data");\n')
        jsx_file.write('compFromBlender();\n')  # Execute function
        jsx_file.write('app.endUndoGroup();\n\n\n')

    # Restore current frame of animation in blender to state before export
    scene.frame_set(frame_current)


##########################################
# ExportJsx class register/unregister
##########################################


from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty


class ExportJsx(bpy.types.Operator, ExportHelper):
    """Export selected cameras and objects animation to After Effects"""
    bl_idname = "export.jsx"
    bl_label = "Export to Adobe After Effects"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".jsx"
    filter_glob: StringProperty(default="*.jsx", options={'HIDDEN'})

    include_animation: BoolProperty(
            name="Animation",
            description="Animate Exported Cameras and Objects",
            default=True,
            )
    include_active_cam: BoolProperty(
            name="Active Camera",
            description="Include Active Camera",
            default=True,
            )
    include_selected_cams: BoolProperty(
            name="Selected Cameras",
            description="Add Selected Cameras",
            default=True,
            )
    include_selected_objects: BoolProperty(
            name="Selected Objects",
            description="Export Selected Objects",
            default=True,
            )
    include_cam_bundles: BoolProperty(
            name="Camera 3D Markers",
            description="Include 3D Markers of Camera Motion Solution for selected cameras",
            default=True,
            )
    include_image_planes: BoolProperty(
            name="Image Planes",
            description="Include image mesh objects",
            default=True,
            )
    include_solids: BoolProperty(
            name="Solids",
            description="Include rectangles as solids",
            default=True,
            )
#    include_ob_bundles = BoolProperty(
#            name="Objects 3D Markers",
#            description="Include 3D Markers of Object Motion Solution for selected cameras",
#            default=True,
#            )
    ae_size: FloatProperty(
            name="Scale",
            description="Size of AE Composition (pixels per 1 BU)",
            default=100.0,
            min=0.0,
            soft_max=10000,
            )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text='Include Cameras and Objects')
        col = box.column(align=True)
        col.prop(self, 'include_active_cam')
        col.prop(self, 'include_selected_cams')
        col.prop(self, 'include_selected_objects')
        col.prop(self, 'include_image_planes')
        col.prop(self, 'include_solids')

        box = layout.box()
        box.label(text='Include Tracking Data')
        box.prop(self, 'include_cam_bundles')
#        box.prop(self, 'include_ob_bundles')

        box = layout.box()
        box.prop(self, 'include_animation')

        box = layout.box()
        box.label(text='Transform')
        box.prop(self, 'ae_size')

    @classmethod
    def poll(cls, context):
        selected = context.selected_objects
        camera = context.scene.camera
        return selected or camera

    def execute(self, context):
        selection = get_selected(context, self.include_active_cam,
                                 self.include_selected_cams,
                                 self.include_selected_objects,
                                 self.include_cam_bundles,
                                 self.include_image_planes,
                                 self.include_solids)
        write_jsx_file(context, self.filepath, selection,
                       self.include_animation, self.ae_size)
        print("\nExport to After Effects Completed")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(
        ExportJsx.bl_idname, text="Adobe After Effects (.jsx)")


def register():
    bpy.utils.register_class(ExportJsx)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportJsx)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
