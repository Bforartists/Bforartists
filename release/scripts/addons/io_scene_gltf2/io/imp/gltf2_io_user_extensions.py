# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

def import_user_extensions(hook_name, gltf_importer, *args):
    for extension in gltf_importer.import_user_extensions:
        hook = getattr(extension, hook_name, None)
        if hook is not None:
            try:
                hook(*args, gltf_importer)
            except Exception as e:
                print(hook_name, "fails on", extension)
                print(str(e))
