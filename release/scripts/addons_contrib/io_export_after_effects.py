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

# <pep8 compliant>

bl_info = {
    "name": "Export: Adobe After Effects (.jsx)",
    "description": "Export cameras, selected objects & camera solution "
        "3D Markers to Adobe After Effects CS3 and above",
    "author": "Bartek Skorupa",
    "version": (0, 0, 68),
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
from math import degrees, floor
from mathutils import Matrix, Vector, Color


def get_comp_data(context):
    """Create list of static blender's data"""
    scene = context.scene
    aspect_x = scene.render.pixel_aspect_x
    aspect_y = scene.render.pixel_aspect_y
    aspect = aspect_x / aspect_y
    start = scene.frame_start
    end = scene.frame_end
    active_cam_frames = get_active_cam_for_each_frame(scene, start, end)
    fps = floor(scene.render.fps / (scene.render.fps_base) * 1000.0) / 1000.0

    return {
        'scn': scene,
        'width': scene.render.resolution_x,
        'height': scene.render.resolution_y,
        'aspect': aspect,
        'fps': fps,
        'start': start,
        'end': end,
        'duration': (end - start + 1.0) / fps,
        'active_cam_frames': active_cam_frames,
        'curframe': scene.frame_current,
        }


def get_active_cam_for_each_frame(scene, start, end):
    """Create list of active camera for each frame in case active camera is set by markers"""
    active_cam_frames = []
    sorted_markers = []
    markers = scene.timeline_markers
    if markers:
        for marker in markers:
            if marker.camera:
                sorted_markers.append([marker.frame, marker])
        sorted_markers = sorted(sorted_markers)

        if sorted_markers:
            for frame in range(start, end + 1):
                for m, marker in enumerate(sorted_markers):
                    if marker[0] > frame:
                        if m != 0:
                            active_cam_frames.append(
                                sorted_markers[m - 1][1].camera)
                        else:
                            active_cam_frames.append(marker[1].camera)
                        break
                    elif m == len(sorted_markers) - 1:
                        active_cam_frames.append(marker[1].camera)
    if not active_cam_frames:
        if scene.camera:
            # in this case active_cam_frames array will have length of 1. This
            # will indicate that there is only one active cam in all frames
            active_cam_frames.append(scene.camera)

    return(active_cam_frames)


def get_selected(context):
    """Create manageable list of selected objects"""
    cameras = []  # List of selected cameras
    solids = []   # List of selected meshes exported as AE solids
    images = []   # List of selected meshes exported as AE AV layers
    lights = []   # List of selected lights exported as AE lights
    nulls = []    # List of selected objects except cameras (will be used to create nulls in AE)
    obs = context.selected_objects

    for ob in obs:
        if ob.type == 'CAMERA':
            cameras.append(ob)

        elif is_image_plane(ob):
            images.append(ob)

        elif is_plane(ob):
            solids.append(ob)

        elif ob.type == 'LIGHT':
            lights.append(ob)

        else:
            nulls.append(ob)

    selection = {
        'cameras': cameras,
        'images': images,
        'solids': solids,
        'lights': lights,
        'nulls': nulls,
        }

    return selection


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

    return '[%f,%f,%f]' % (color[0], color[1], color[2])


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
    """
    if not is_plane(obj):
        return False

    if not len(obj.material_slots):
        return False

    mat = get_first_material(obj)
    if mat is None:
        return False

    img = get_image_node(mat)
    if img is None:
        return False

    if len(obj.data.vertices) == 4:
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
    for p_i, p in enumerate(obj.data.uv_layers.active.data):
        if p.uv == Vector((0, 0)):
            p0 = p_i
        elif p.uv == Vector((1, 0)):
            px = p_i
        elif p.uv == Vector((0, 1)):
            py = p_i

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
    name = "_" + name
    '''
    # Digits are not allowed at beginning of AE vars names.
    # This section is commented, as "_" is added at beginning of names anyway.
    # Placeholder for this name modification is left so that it's not ignored if needed
    if name[0].isdigit():
        name = "_" + name
    '''
    name = bpy.path.clean_name(name)
    name = name.replace("-", "_")

    return name


def convert_transform_matrix(matrix, width, height, aspect,
                             x_rot_correction=False, ae_size=100.0):
    """Convert from Blender's Location, Rotation and Scale
    to AE's Position, Rotation/Orientation and Scale

    This function will be called for every object for every frame
    """

    scale_mat = Matrix.Scale(width, 4)

    # Get blender transform data for ob
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
    # If not x_rot_correction
    rx =  degrees(b_rot.x)  # AE's X orientation =  blender's X rotation if 'ZYX' euler.
    ry = -degrees(b_rot.y)  # AE's Y orientation = -blender's Y rotation if 'ZYX' euler
    rz = -degrees(b_rot.z)  # AE's Z orientation = -blender's Z rotation if 'ZYX' euler
    if x_rot_correction:
        # In Blender, ob of zero rotation lays on floor.
        # In AE, layer of zero orientation "stands"
        rx -= 90.0
    # Convert scale to AE scale. ae_size is a global multiplier.
    sx = b_scale.x * ae_size
    sy = b_scale.y * ae_size
    sz = b_scale.z * ae_size

    return x, y, z, rx, ry, rz, sx, sy, sz

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
# If camera.sensor_fit is set to 'AUTO'
# and the vertical size is greater than the horizontal size:
#     sensor = camera.data.sensor_width, dimension = width.
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
    if (camera.data.sensor_fit == 'VERTICAL'
            or camera.data.sensor_fit == 'AUTO'
            and (width / height) * aspect < 0):
        sensor = camera.data.sensor_height
        dimension = height
    else:
        sensor = camera.data.sensor_width
        dimension = width

    zoom = camera.data.lens * dimension / sensor * aspect

    return zoom

# convert object bundle's matrix. Not ready yet. Temporarily not active
# def get_ob_bundle_matrix_world(cam_matrix_world, bundle_matrix):
#    matrix = cam_matrix_basis
#    return matrix


def write_jsx_file(file, data, selection, include_animation,
                   include_active_cam, include_selected_cams,
                   include_selected_objects, include_cam_bundles,
                   include_image_planes, ae_size):
    """jsx script for AE creation"""

    print("\n---------------------------\n- Export to After Effects -\n---------------------------")
    # Store the current frame to restore it at the end of export
    curframe = data['curframe']
    # Create array which will contain all keyframes values
    js_data = {
        'times': '',
        'cameras': {},
        'images': {},
        'solids': {},
        'lights': {},
        'nulls': {},
        'bundles_cam': {},
        'bundles_ob': {},  # not ready yet
        }

    # Create structure for active camera/cameras
    active_cam_name = ''
    if include_active_cam and data['active_cam_frames']:
        # Check if more than one active cam exists
        # (True if active cams set by markers)
        if len(data['active_cam_frames']) == 1:
            # Take name of the only active camera in scene
            name_ae = convert_name(data['active_cam_frames'][0].name)
        else:
            name_ae = 'Active_Camera'
        # Store name to be used when creating keyframes for active cam
        active_cam_name = name_ae
        js_data['cameras'][name_ae] = {
            'position': '',
            'position_static': '',
            'position_anim': False,
            'orientation': '',
            'orientation_static': '',
            'orientation_anim': False,
            'zoom': '',
            'zoom_static': '',
            'zoom_anim': False,
            }

    # Create camera structure for selected cameras
    if include_selected_cams:
        for obj in selection['cameras']:
            # More than one camera can be selected
            if convert_name(obj.name) != active_cam_name:
                name_ae = convert_name(obj.name)
                js_data['cameras'][name_ae] = {
                    'position': '',
                    'position_static': '',
                    'position_anim': False,
                    'orientation': '',
                    'orientation_static': '',
                    'orientation_anim': False,
                    'zoom': '',
                    'zoom_static': '',
                    'zoom_anim': False,
                    }

    # Create structure for solids
    for obj in selection['solids']:
        name_ae = convert_name(obj.name)
        js_data['solids'][name_ae] = {
            'position': '',
            'position_static': '',
            'position_anim': False,
            'orientation': '',
            'orientation_static': '',
            'orientation_anim': False,
            'scale': '',
            'scale_static': '',
            'scale_anim': False,
            }

    # Create structure for images
    for obj in selection['images']:
        name_ae = convert_name(obj.name)
        js_data['images'][name_ae] = {
            'position': '',
            'position_static': '',
            'position_anim': False,
            'orientation': '',
            'orientation_static': '',
            'orientation_anim': False,
            'scale': '',
            'scale_static': '',
            'scale_anim': False,
            'filepath': '',
        }

    # Create structure for lights
    for obj in selection['lights']:
        if include_selected_objects:
            name_ae = obj.data.type + convert_name(obj.name)
            js_data['lights'][name_ae] = {
                'type': obj.data.type,
                'intensity': '',
                'intensity_static': '',
                'intensity_anim': False,
                'Cone Angle': '',
                'Cone Angle_static': '',
                'Cone Angle_anim': False,
                'Cone Feather': '',
                'Cone Feather_static': '',
                'Cone Feather_anim': False,
                'Color': '',
                'Color_static': '',
                'Color_anim': False,
                'position': '',
                'position_static': '',
                'position_anim': False,
                'orientation': '',
                'orientation_static': '',
                'orientation_anim': False,
                }

    # Create structure for nulls
    # nulls representing blender's obs except cameras, lights and solids
    for obj in selection['nulls']:
        if include_selected_objects:
            name_ae = convert_name(obj.name)
            js_data['nulls'][name_ae] = {
                'position': '',
                'position_static': '',
                'position_anim': False,
                'orientation': '',
                'orientation_static': '',
                'orientation_anim': False,
                'scale': '',
                'scale_static': '',
                'scale_anim': False,
                }

    # Create structure for cam bundles including positions
    # (cam bundles don't move)
    if include_cam_bundles:
        # Go through each selected camera and active cameras
        selected_cams = []
        active_cams = []
        if include_active_cam:
            active_cams = data['active_cam_frames']
        if include_selected_cams:
            for cam in selection['cameras']:
                selected_cams.append(cam)
        # List of cameras that will be checked for 'CAMERA SOLVER'
        cams = list(set.union(set(selected_cams), set(active_cams)))

        for cam in cams:
            # Go through each constraints of this camera
            for constraint in cam.constraints:
                # Does the camera have a Camera Solver constraint
                if constraint.type == 'CAMERA_SOLVER':
                    # Which movie clip does it use
                    if constraint.use_active_clip:
                        clip = data['scn'].active_clip
                    else:
                        clip = constraint.clip

                    # Go through each tracking point
                    for track in clip.tracking.tracks:
                        # Does this tracking point have a bundle
                        # (has its 3D position been solved)
                        if track.has_bundle:
                            # Get the name of the tracker
                            name_ae = convert_name(str(cam.name) + '__' +
                                                   str(track.name))
                            js_data['bundles_cam'][name_ae] = {
                                'position': '',
                                }
                            # Bundles are in camera space.
                            # Transpose to world space
                            matrix = Matrix.Translation(cam.matrix_basis.copy()
                                                        @ track.bundle)
                            # Convert the position into AE space
                            ae_transform = (convert_transform_matrix(
                                matrix, data['width'], data['height'],
                                data['aspect'], False, ae_size))
                            js_data['bundles_cam'][name_ae]['position'] += ('[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2]))

    # Get all keyframes for each object and store in dico
    if include_animation:
        end = data['end'] + 1
    else:
        end = data['start'] + 1
    for frame in range(data['start'], end):
        print("working on frame: " + str(frame))
        data['scn'].frame_set(frame)

        # Get time for this loop
        js_data['times'] += '%f,' % ((frame - data['start']) / data['fps'])

        # Keyframes for active camera/cameras
        if include_active_cam and data['active_cam_frames'] != []:
            if len(data['active_cam_frames']) == 1:
                cur_cam_index = 0
            else:
                cur_cam_index = frame - data['start']
            active_cam = data['active_cam_frames'][cur_cam_index]
            # Get cam name
            name_ae = active_cam_name
            # Convert cam transform properties to AE space
            ae_transform = (convert_transform_matrix(
                active_cam.matrix_world.copy(), data['width'], data['height'],
                data['aspect'], True, ae_size))
            # Convert Blender's lens to AE's zoom in pixels
            zoom = convert_lens(active_cam, data['width'], data['height'],
                                data['aspect'])
            # Store all values in dico
            position = '[%f,%f,%f],' % (ae_transform[0], ae_transform[1],
                                        ae_transform[2])
            orientation = '[%f,%f,%f],' % (ae_transform[3], ae_transform[4],
                                           ae_transform[5])
            zoom = '%f,' % (zoom)
            js_camera = js_data['cameras'][name_ae]
            js_camera['position'] += position
            js_camera['orientation'] += orientation
            js_camera['zoom'] += zoom
            # Check if properties change values compared to previous frame
            # If property don't change through out the whole animation,
            # keyframes won't be added
            if frame != data['start']:
                if position != js_camera['position_static']:
                    js_camera['position_anim'] = True
                if orientation != js_camera['orientation_static']:
                    js_camera['orientation_anim'] = True
                if zoom != js_camera['zoom_static']:
                    js_camera['zoom_anim'] = True
            js_camera['position_static'] = position
            js_camera['orientation_static'] = orientation
            js_camera['zoom_static'] = zoom

        # Keyframes for selected cameras
        if include_selected_cams:
            for obj in selection['cameras']:
                if convert_name(obj.name) != active_cam_name:
                    # Get cam name
                    name_ae = convert_name(obj.name)
                    # Convert cam transform properties to AE space
                    ae_transform = convert_transform_matrix(
                        obj.matrix_world.copy(), data['width'],
                        data['height'], data['aspect'], True, ae_size)
                    # Convert Blender's lens to AE's zoom in pixels
                    zoom = convert_lens(obj, data['width'], data['height'],
                                        data['aspect'])
                    # Store all values in dico
                    position = '[%f,%f,%f],' % (ae_transform[0],
                                                ae_transform[1],
                                                ae_transform[2])
                    orientation = '[%f,%f,%f],' % (ae_transform[3],
                                                   ae_transform[4],
                                                   ae_transform[5])
                    zoom = '%f,' % (zoom)
                    js_camera = js_data['cameras'][name_ae]
                    js_camera['position'] += position
                    js_camera['orientation'] += orientation
                    js_camera['zoom'] += zoom
                    # Check if properties change values compared to previous frame
                    # If property don't change through out the whole animation,
                    # keyframes won't be added
                    if frame != data['start']:
                        if position != js_camera['position_static']:
                            js_camera['position_anim'] = True
                        if orientation != js_camera['orientation_static']:
                            js_camera['orientation_anim'] = True
                        if zoom != js_camera['zoom_static']:
                            js_camera['zoom_anim'] = True
                    js_camera['position_static'] = position
                    js_camera['orientation_static'] = orientation
                    js_camera['zoom_static'] = zoom

        # Keyframes for all solids.
        if include_selected_objects:
            for obj in selection['solids']:
                # Get object name
                name_ae = convert_name(obj.name)
                # Convert obj transform properties to AE space
                plane_matrix = get_plane_matrix(obj)
                # Scale plane to account for AE's transforms
                plane_matrix = plane_matrix @ Matrix.Scale(100.0 / data['width'], 4)
                ae_transform = convert_transform_matrix(
                    plane_matrix, data['width'], data['height'],
                    data['aspect'], True, ae_size)
                # Store all values in dico
                position = '[%f,%f,%f],' % (ae_transform[0],
                                            ae_transform[1],
                                            ae_transform[2])
                orientation = '[%f,%f,%f],' % (ae_transform[3],
                                               ae_transform[4],
                                               ae_transform[5])
                # plane_width, plane_height, _ = plane_matrix.to_scale()
                scale = '[%f,%f,%f],' % (ae_transform[6],
                                         ae_transform[7] * data['width'] / data['height'],
                                         ae_transform[8])
                js_solid = js_data['solids'][name_ae]
                js_solid['color'] = get_plane_color(obj)
                js_solid['width'] = data['width']
                js_solid['height'] = data['height']
                js_solid['position'] += position
                js_solid['orientation'] += orientation
                js_solid['scale'] += scale
                # Check if properties change values compared to previous frame
                # If property don't change through out the whole animation,
                # keyframes won't be added
                if frame != data['start']:
                    if position != js_solid['position_static']:
                        js_solid['position_anim'] = True
                    if orientation != js_solid['orientation_static']:
                        js_solid['orientation_anim'] = True
                    if scale != js_solid['scale_static']:
                        js_solid['scale_anim'] = True
                js_solid['position_static'] = position
                js_solid['orientation_static'] = orientation
                js_solid['scale_static'] = scale

        # Keyframes for all lights.
        if include_selected_objects:
            for obj in selection['lights']:
                # Get object name
                name_ae = obj.data.type + convert_name(obj.name)
                type = obj.data.type
                # Convert ob transform properties to AE space
                ae_transform = convert_transform_matrix(
                    obj.matrix_world.copy(), data['width'], data['height'],
                    data['aspect'], True, ae_size)
                color = obj.data.color
                # Store all values in dico
                position = '[%f,%f,%f],' % (ae_transform[0], ae_transform[1],
                                            ae_transform[2])
                orientation = '[%f,%f,%f],' % (ae_transform[3],
                                               ae_transform[4],
                                               ae_transform[5])
                energy = '[%f],' % (obj.data.energy * 100.0)
                color = '[%f,%f,%f],' % (color[0], color[1], color[2])
                js_light = js_data['lights'][name_ae]
                js_light['position'] += position
                js_light['orientation'] += orientation
                js_light['intensity'] += energy
                js_light['Color'] += color
                # Check if properties change values compared to previous frame
                # If property don't change through out the whole animation,
                # keyframes won't be added
                if frame != data['start']:
                    if position != js_light['position_static']:
                        js_light['position_anim'] = True
                    if orientation != js_light['orientation_static']:
                        js_light['orientation_anim'] = True
                    if energy != js_light['intensity_static']:
                        js_light['intensity_anim'] = True
                    if color != js_light['Color_static']:
                        js_light['Color_anim'] = True
                js_light['position_static'] = position
                js_light['orientation_static'] = orientation
                js_light['intensity_static'] = energy
                js_light['Color_static'] = color
                if type == 'SPOT':
                    cone_angle = '[%f],' % (degrees(obj.data.spot_size))
                    cone_feather = '[%f],' % (obj.data.spot_blend * 100.0)
                    js_light['Cone Angle'] += cone_angle
                    js_light['Cone Feather'] += cone_feather
                    # Check if properties change values compared to previous frame
                    # If property don't change through out the whole animation,
                    # keyframes won't be added
                    if frame != data['start']:
                        if cone_angle != js_light['Cone Angle_static']:
                            js_light['Cone Angle_anim'] = True
                        if cone_feather != js_light['Cone Feather_static']:
                            js_light['Cone Feather_anim'] = True
                    js_light['Cone Angle_static'] = cone_angle
                    js_light['Cone Feather_static'] = cone_feather

        # Keyframes for all nulls
        if include_selected_objects:
            for obj in selection['nulls']:
                # Get object name
                name_ae = convert_name(obj.name)
                # Convert obj transform properties to AE space
                ae_transform = convert_transform_matrix(obj.matrix_world.copy(), data['width'], data['height'], data['aspect'], True, ae_size)
                # Store all values in dico
                position = '[%f,%f,%f],' % (ae_transform[0], ae_transform[1],
                                            ae_transform[2])
                orientation = '[%f,%f,%f],' % (ae_transform[3], ae_transform[4],
                                               ae_transform[5])
                scale = '[%f,%f,%f],' % (ae_transform[6], ae_transform[7],
                                         ae_transform[8])
                js_null = js_data['nulls'][name_ae]
                js_null['position'] += position
                js_null['orientation'] += orientation
                js_null['scale'] += scale
                # Check if properties change values compared to previous frame
                # If property don't change through out the whole animation,
                # keyframes won't be added
                if frame != data['start']:
                    if position != js_null['position_static']:
                        js_null['position_anim'] = True
                    if orientation != js_null['orientation_static']:
                        js_null['orientation_anim'] = True
                    if scale != js_null['scale_static']:
                        js_null['scale_anim'] = True
                js_null['position_static'] = position
                js_null['orientation_static'] = orientation
                js_null['scale_static'] = scale

        # Keyframes for all images
        if include_image_planes:
            for obj in selection['images']:
                # Get object name
                name_ae = convert_name(obj.name)
                # Convert obj transform properties to AE space
                plane_matrix = get_image_plane_matrix(obj)
                # Scale plane to account for AE's transforms
                plane_matrix = plane_matrix @ Matrix.Scale(100.0 / data['width'], 4)
                ae_transform = convert_transform_matrix(
                    plane_matrix, data['width'], data['height'],
                    data['aspect'], True, ae_size)
                # Store all values in dico
                position = '[%f,%f,%f],' % (ae_transform[0],
                                            ae_transform[1],
                                            ae_transform[2])
                orientation = '[%f,%f,%f],' % (ae_transform[3],
                                               ae_transform[4],
                                               ae_transform[5])
                image_width, image_height = get_image_size(obj)
                ratio_to_comp = image_width / data['width']
                scale = '[%f,%f,%f],' % (ae_transform[6] / ratio_to_comp,
                                         ae_transform[7] / ratio_to_comp
                                         * image_width / image_height,
                                         ae_transform[8])
                js_image = js_data['images'][name_ae]
                js_image['position'] += position
                js_image['orientation'] += orientation
                js_image['scale'] += scale
                # Check if properties change values compared to previous frame
                # If property don't change through out the whole animation,
                # keyframes won't be added
                if frame != data['start']:
                    if position != js_image['position_static']:
                        js_image['position_anim'] = True
                    if orientation != js_image['orientation_static']:
                        js_image['orientation_anim'] = True
                    if scale != js_image['scale_static']:
                        js_image['scale_anim'] = True
                js_image['position_static'] = position
                js_image['orientation_static'] = orientation
                js_image['scale_static'] = scale
                js_image['filepath'] = get_image_filepath(obj)

        # keyframes for all object bundles. Not ready yet.
        #
        #
        #

    # ---- write JSX file
    jsx_file = open(file, 'w')

    # Make the jsx executable in After Effects (enable double click on jsx)
    jsx_file.write('#target AfterEffects\n\n')
    # Script's header
    jsx_file.write('/**************************************\n')
    jsx_file.write('Scene : %s\n' % data['scn'].name)
    jsx_file.write('Resolution : %i x %i\n' % (data['width'], data['height']))
    jsx_file.write('Duration : %f\n' % (data['duration']))
    jsx_file.write('FPS : %f\n' % (data['fps']))
    jsx_file.write('Date : %s\n' % datetime.datetime.now())
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
    jsx_file.write('\nvar compName = prompt("Blender Comp\'s Name \\nEnter Name of newly created Composition","%s","Composition\'s Name");\n' % comp_name)
    jsx_file.write('if (compName){')
    # Continue only if comp name is given. If not - terminate
    jsx_file.write(
        '\nvar newComp = app.project.items.addComp(compName, %i, %i, %f, %f, %f);'
        % (data['width'], data['height'], data['aspect'],
           data['duration'], data['fps']))
    jsx_file.write('\nnewComp.displayStartTime = %f;\n\n\n'
                   % ((data['start'] + 1.0) / data['fps']))

    # Create camera bundles (nulls)
    jsx_file.write('// **************  CAMERA 3D MARKERS  **************\n\n')
    for name_ae, obj in js_data['bundles_cam'].items():
        jsx_file.write('var %s = newComp.layers.addNull();\n' % (name_ae))
        jsx_file.write('%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write('%s.source.name = "%s";\n' % (name_ae, name_ae))
        jsx_file.write('%s.property("position").setValue(%s);\n\n'
                       % (name_ae, obj['position']))
    jsx_file.write('\n')

    # Create object bundles (not ready yet)

    # Create objects (nulls)
    jsx_file.write('// **************  OBJECTS  **************\n\n')
    for name_ae, obj in js_data['nulls'].items():
        jsx_file.write('var %s = newComp.layers.addNull();\n' % (name_ae))
        jsx_file.write('%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write('%s.source.name = "%s";\n' % (name_ae, name_ae))
        # Set values of properties, add keyframes only where needed
        for prop in ("position", "orientation", "scale"):
            if include_animation and obj[prop + '_anim']:
                jsx_file.write(
                    '%s.property("%s").setValuesAtTimes([%s],[%s]);\n'
                    % (name_ae, prop, js_data['times'], obj[prop]))
            else:
                jsx_file.write(
                    '%s.property("%s").setValue(%s);\n'
                    % (name_ae, prop, obj[prop + '_static']))
        jsx_file.write('\n')
    jsx_file.write('\n')

    # Create solids
    jsx_file.write('// **************  SOLIDS  **************\n\n')
    for name_ae, obj in js_data['solids'].items():
        jsx_file.write(
            'var %s = newComp.layers.addSolid(%s,"%s",%i,%i,%f);\n' % (
                name_ae,
                obj['color'],
                name_ae,
                obj['width'],
                obj['height'],
                1.0))
        jsx_file.write(
            '%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write(
            '%s.source.name = "%s";\n' % (name_ae, name_ae))
        # Set values of properties, add keyframes only where needed
        for prop in ("position", "orientation", "scale"):
            if include_animation and obj[prop + '_anim']:
                jsx_file.write(
                    '%s.property("%s").setValuesAtTimes([%s],[%s]);\n'
                    % (name_ae, prop, js_data['times'], obj[prop]))
            else:
                jsx_file.write(
                    '%s.property("%s").setValue(%s);\n'
                    % (name_ae, prop, obj[prop + '_static']))
        jsx_file.write('\n')
    jsx_file.write('\n')

    # Create images
    jsx_file.write('// **************  IMAGES  **************\n\n')
    for name_ae, obj in js_data['images'].items():
        jsx_file.write(
            'var newFootage = app.project.importFile(new ImportOptions(File("%s")))\n'
            % (obj['filepath']))
        jsx_file.write(
            'var %s = newComp.layers.add(newFootage);\n' % (name_ae))
        jsx_file.write(
            '%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write(
            '%s.source.name = "%s";\n' % (name_ae, name_ae))
        # Set values of properties, add keyframes only where needed
        for prop in ("position", "orientation", "scale"):
            if include_animation and obj[prop + '_anim']:
                jsx_file.write(
                    '%s.property("%s").setValuesAtTimes([%s],[%s]);\n'
                    % (name_ae, prop, js_data['times'], obj[prop]))
            else:
                jsx_file.write(
                    '%s.property("%s").setValue(%s);\n'
                    % (name_ae, prop, obj[prop + '_static']))
        jsx_file.write('\n')
    jsx_file.write('\n')

    # Create lights
    jsx_file.write('// **************  LIGHTS  **************\n\n')
    for name_ae, obj in js_data['lights'].items():
        jsx_file.write(
            'var %s = newComp.layers.addLight("%s", [0.0, 0.0]);\n'
            % (name_ae, name_ae))
        jsx_file.write(
            '%s.autoOrient = AutoOrientType.NO_AUTO_ORIENT;\n'
            % name_ae)
        # Set values of properties, add keyframes only where needed
        props = ["position", "orientation", "intensity", "Color"]
        if obj['type'] == 'SPOT':
            props.extend(("Cone Angle", "Cone Feather"))
        for prop in props:
            if include_animation and obj[prop + '_anim']:
                jsx_file.write(
                    '%s.property("%s").setValuesAtTimes([%s],[%s]);\n'
                    % (name_ae, prop, js_data['times'], obj[prop]))
            else:
                jsx_file.write(
                    '%s.property("%s").setValue(%s);\n'
                    % (name_ae, prop, obj[prop + '_static']))
        jsx_file.write('\n')
    jsx_file.write('\n')

    # Create cameras
    jsx_file.write('// **************  CAMERAS  **************\n\n')
    for name_ae, obj in js_data['cameras'].items():
        # More than one camera can be selected
        jsx_file.write(
            'var %s = newComp.layers.addCamera("%s",[0,0]);\n'
            % (name_ae, name_ae))
        jsx_file.write(
            '%s.autoOrient = AutoOrientType.NO_AUTO_ORIENT;\n'
            % name_ae)

        # Set values of properties, add keyframes only where needed
        for prop in ("position", "orientation", "zoom"):
            if include_animation and obj[prop + '_anim']:
                jsx_file.write(
                    '%s.property("%s").setValuesAtTimes([%s],[%s]);\n'
                    % (name_ae, prop, js_data['times'], obj[prop]))
            else:
                jsx_file.write(
                    '%s.property("%s").setValue(%s);\n'
                    % (name_ae, prop, obj[prop + '_static']))
        jsx_file.write('\n')
    jsx_file.write('\n')

    # Exit import if no comp name given
    jsx_file.write('\n}else{alert ("Exit Import Blender animation data \\nNo Comp name has been chosen","EXIT")};')
    # Close function
    jsx_file.write("}\n\n\n")
    # Execute function. Wrap in "undo group" for easy undoing import process
    jsx_file.write('app.beginUndoGroup("Import Blender animation data");\n')
    jsx_file.write('compFromBlender();\n')  # Execute function
    jsx_file.write('app.endUndoGroup();\n\n\n')
    jsx_file.close()

    # Set current frame of animation in blender to state before export
    data['scn'].frame_set(curframe)


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
        box.prop(self, 'include_active_cam')
        box.prop(self, 'include_selected_cams')
        box.prop(self, 'include_selected_objects')
        box.prop(self, 'include_image_planes')
        box = layout.box()
        box.prop(self, 'include_animation')
        box = layout.box()
        box.label(text='Transform')
        box.prop(self, 'ae_size')
        box = layout.box()
        box.label(text='Include Tracking Data:')
        box.prop(self, 'include_cam_bundles')
#        box.prop(self, 'include_ob_bundles')

    @classmethod
    def poll(cls, context):
        selected = context.selected_objects
        camera = context.scene.camera
        return selected or camera

    def execute(self, context):
        data = get_comp_data(context)
        selection = get_selected(context)
        write_jsx_file(self.filepath, data, selection, self.include_animation,
                       self.include_active_cam, self.include_selected_cams,
                       self.include_selected_objects, self.include_cam_bundles,
                       self.include_image_planes, self.ae_size)
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
