#
# Copyright 2011-2013 Blender Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# <pep8 compliant>


def init():
    import bpy
    import _cycles
    import os.path

    path = os.path.dirname(__file__)
    user_path = os.path.dirname(os.path.abspath(bpy.utils.user_resource('CONFIG', '')))

    _cycles.init(path, user_path, bpy.app.background)


def create(engine, data, scene, region=None, v3d=None, rv3d=None, preview_osl=False):
    import bpy
    import _cycles

    data = data.as_pointer()
    userpref = bpy.context.user_preferences.as_pointer()
    scene = scene.as_pointer()
    if region:
        region = region.as_pointer()
    if v3d:
        v3d = v3d.as_pointer()
    if rv3d:
        rv3d = rv3d.as_pointer()

    engine.session = _cycles.create(engine.as_pointer(), userpref, data, scene, region, v3d, rv3d, preview_osl)


def free(engine):
    if hasattr(engine, "session"):
        if engine.session:
            import _cycles
            _cycles.free(engine.session)
        del engine.session


def render(engine):
    import _cycles
    if hasattr(engine, "session"):
        _cycles.render(engine.session)


def bake(engine, obj, pass_type, object_id, pixel_array, num_pixels, depth, result):
    import _cycles
    session = getattr(engine, "session", None)
    if session is not None:
        _cycles.bake(engine.session, obj.as_pointer(), pass_type, object_id, pixel_array.as_pointer(), num_pixels, depth, result.as_pointer())


def reset(engine, data, scene):
    import _cycles
    data = data.as_pointer()
    scene = scene.as_pointer()
    _cycles.reset(engine.session, data, scene)


def update(engine, data, scene):
    import _cycles
    _cycles.sync(engine.session)


def draw(engine, region, v3d, rv3d):
    import _cycles
    v3d = v3d.as_pointer()
    rv3d = rv3d.as_pointer()

    # draw render image
    _cycles.draw(engine.session, v3d, rv3d)


def available_devices():
    import _cycles
    return _cycles.available_devices()


def with_osl():
    import _cycles
    return _cycles.with_osl


def with_network():
    import _cycles
    return _cycles.with_network


def system_info():
    import _cycles
    return _cycles.system_info()
