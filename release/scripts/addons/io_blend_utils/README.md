
Bundling BAM with Blender
-------------------------

Blender is bundled with a version of [BAM](https://pypi.python.org/pypi/blender-bam/).
To update this version, first build a new `wheel <http://pythonwheels.com/>`_ file in
BAM itself:

    python3 setup.py bdist_wheel

Then copy this wheel to Blender:

    cp dist/blender_bam-xxx.whl /path/to/blender/release/scripts/addons/io_blend_utils/

Remove old wheels that are still in `/path/to/blender/release/scripts/addons/io_blend_utils/`
before committing.


Running bam-pack from the wheel
-------------------------------

This is the way that Blender runs bam-pack:

    PYTHONPATH=./path/to/blender_bam-xxx.whl python3 -m bam.pack

