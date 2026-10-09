# SPDX-FileCopyrightText: 2024 Vincent Marchetti, Bujus_Krachus
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
_logger = logging.getLogger("export_x3d.material_node_search")

"""
functions implementing searching the node tree for Blender materials in search
of particular nodes enabling export of material properties into other formats
"""

# values of bl_idname for shader nodes to be located
# reference Python API list of subclasses of ShaderNode
# at https://docs.blender.org/api/current/bpy.types.ShaderNode.html#bpy.types.ShaderNode
class _ShaderNodeTypes:
    MATERIAL_OUTPUT = "ShaderNodeOutputMaterial"
    BSDF_PRINCIPLED = "ShaderNodeBsdfPrincipled"
    IMAGE_TEXTURE = "ShaderNodeTexImage"
    EMISSION = "ShaderNodeEmission"
    DIFFUSE_BSDF = "ShaderNodeBsdfDiffuse"
    MAPPING = "ShaderNodeMapping"

def _find_node_by_idname(node_tree, idname, find_all=False):
    """
    Find nodes by idname in a node tree.

    Each node is assumed to be an instance of Node(bpy_struct)
    https://docs.blender.org/api/current/bpy.types.Node.html

    The idname is searched for in the Node instance member bl_idname
    https://docs.blender.org/api/current/bpy.types.Node.html#bpy.types.Node.bl_idname
    and is generally some string version of the name of the subclass

    See https://docs.blender.org/api/current/bpy.types.ShaderNode.html for list of
    ShaderNode subclasses

    Args:
        node_tree: The node tree to search.
        idname (str): Identifier of the node type to find.
        find_all (bool): If True, return all matching nodes; otherwise, return the first match.

    Returns:
        list | Node | None: List of matching nodes if find_all is True;
                             first matching node if find_all is False;
                             None if no match is found.
    """
    if not node_tree or not hasattr(node_tree, "nodes"):
        _logger.warning("Invalid or missing node tree.")
        return None

    matches = (nd for nd in node_tree.nodes if nd.bl_idname == idname)
    if find_all:
        results = list(matches)
        _logger.debug(f"Found {len(results)} nodes of type {idname}.")
        return results
    else:
        result = next(matches, None)
        if result is None:
            _logger.debug(f"No nodes of type {idname} found.")
        return result


def _recursive_find_node_by_idname(node_tree, idname):
    """
    Recursively searches a node tree, including within NodeGroups, for nodes of the given idname.

    Args:
        node_tree: The node tree to search.
        idname (str): The idname of the node to find.

    Returns:
        Node | None: The first matching node found, or None if no match.
    """
    if not node_tree or not hasattr(node_tree, "nodes"):
        _logger.warning("Invalid or missing node tree.")
        return None

    for node in node_tree.nodes:
        if node.bl_idname == idname:
            return node
        if node.bl_idname == "ShaderNodeGroup" and hasattr(node, "node_tree"):
            found = _recursive_find_node_by_idname(node.node_tree, idname)
            if found:
                return found
    return None


def imageTexture_in_material(material):
    """
    Identifies any ImageTexture node in the material's node tree, recursively including NodeGroups.
    https://docs.blender.org/api/current/bpy.types.ShaderNodeTexImage.html

    Args:
        material: An instance of Material(ID)
                  https://docs.blender.org/api/current/bpy.types.Material.html

    Returns:
        ShaderNodeTexImage | None: The first matching ShaderNodeTexImage node.
    """
    if not material: # when no material is set
        return None

    _logger.debug(f"Evaluating image in material {material.name}")

    # Search for any IMAGE_TEXTURE node recursively in the material's node tree
    image_texture = _recursive_find_node_by_idname(material.node_tree, _ShaderNodeTypes.IMAGE_TEXTURE)
    if image_texture is None:
        _logger.debug(f"{_ShaderNodeTypes.IMAGE_TEXTURE} not found in material {material.name}")
        return None

    _logger.debug(f"Located image texture node {image_texture}")
    return image_texture

def get_vector_mapping_properties(image_texture):
    """
    Finds the transformation properties (rotation, scale, translation) of a ShaderNodeMapping node
    connected to the ImageTexture node.

    Args:
        image_texture: The ImageTexture node instance.

    Returns:
        dict | None: A dictionary with keys 'rotation', 'scale', 'translation', containing corresponding
                     values as tuples, or None if no Mapping node is connected.
    """
    if not image_texture:
        _logger.warning("No image texture node provided.")
        return None

    mapping_node = next(
        (link.from_node for input in image_texture.inputs for link in input.links
         if link.from_node.bl_idname == _ShaderNodeTypes.MAPPING),
        None
    )

    if mapping_node:
        properties = {
            "rotation": mapping_node.inputs["Rotation"].default_value[:3] if "Rotation" in mapping_node.inputs else (0.0, 0.0, 0.0),
            "scale": mapping_node.inputs["Scale"].default_value[:3] if "Scale" in mapping_node.inputs else (1.0, 1.0, 1.0),
            "translation": mapping_node.inputs["Location"].default_value[:3] if "Location" in mapping_node.inputs else (0.0, 0.0, 0.0),
        }
        _logger.debug(f"Found mapping properties {properties} in mapping node {mapping_node}")
        return properties

    _logger.debug("No mapping node connected to image texture.")
    return None

def get_movie_texture_properties(image_texture):
    """
    Retrieves properties of a movie texture if the image texture is a movie.

    Args:
        image_texture: The ImageTexture node instance.

    Returns:
        dict | None: A dictionary containing movie-specific properties
                     ('use_cyclic', 'use_auto_refresh', 'frame_start', 'frame_duration')
                     or None if not a movie texture.
    """
    if not image_texture or not hasattr(image_texture, 'image') or not image_texture.image:
        _logger.warning("No valid image data found in the node.")
        return None

    if image_texture.image.source != 'MOVIE':
        _logger.debug(f"Image {image_texture.image.filepath} is not a movie texture.")
        return None

    image = image_texture.image_user

    properties = {
        "use_cyclic": image.use_cyclic,
        "use_auto_refresh": image.use_auto_refresh,
        "frame_start": image.frame_start,
        "frame_duration": image.frame_duration,
    }
    _logger.debug(f"Movie texture properties: {properties}")
    return properties

def get_emissive_color(material):
    """
    Finds the emissive color in the material's node tree.

    Args:
        material: An instance of Material(ID).

    Returns:
        tuple | None: RGB values of the emissive color and alpha if Principled, or None if not found.
    """
    emission_node = _recursive_find_node_by_idname(material.node_tree, _ShaderNodeTypes.EMISSION)
    if emission_node and hasattr(emission_node.inputs.get("Color"), "default_value"):
        return tuple(emission_node.inputs["Color"].default_value[:4]) # reuse color alpha

    bsdf_node = _recursive_find_node_by_idname(material.node_tree, _ShaderNodeTypes.BSDF_PRINCIPLED)
    if bsdf_node and hasattr(bsdf_node.inputs.get("Emission"), "default_value"):
        alpha_value = bsdf_node.inputs["Alpha"].default_value # use alpha socket
        return tuple(bsdf_node.inputs["Emission"].default_value[:3])  + (alpha_value,)

    return None


def get_diffuse_color(material):
    """
    Finds the diffuse color in the material's node tree.

    Args:
        material: An instance of Material(ID).

    Returns:
        tuple | None: RGB values of the diffuse color and alpha if Principled, or None if not found.
    """
    diffuse_node = _recursive_find_node_by_idname(material.node_tree, _ShaderNodeTypes.DIFFUSE_BSDF)
    if diffuse_node and hasattr(diffuse_node.inputs.get("Color"), "default_value"):
        return tuple(diffuse_node.inputs["Color"].default_value[:4]) # reuse color alpha

    bsdf_node = _recursive_find_node_by_idname(material.node_tree, _ShaderNodeTypes.BSDF_PRINCIPLED)
    if bsdf_node and hasattr(bsdf_node.inputs.get("Base Color"), "default_value"):
        alpha_value = bsdf_node.inputs["Alpha"].default_value # use alpha socket
        return tuple(bsdf_node.inputs["Base Color"].default_value[:3]) + (alpha_value,)

    return None
