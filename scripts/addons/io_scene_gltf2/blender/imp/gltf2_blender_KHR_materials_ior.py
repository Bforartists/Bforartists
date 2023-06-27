# SPDX-FileCopyrightText: 2018-2021 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

from ...io.com.gltf2_io_constants import GLTF_IOR

def ior(mh, ior_socket):
    try:
        ext = mh.pymat.extensions['KHR_materials_ior']
    except Exception:
        return
    ior = ext.get('ior', GLTF_IOR)
    ior_socket.default_value = ior
