# This script is an example of how you can run blender from the command line (in background mode with no interface)
# to automate tasks, in this example it creates a text object, camera and light, then renders and/or saves it.
# This example also shows how you can parse command line options to python scripts.
#
# Example usage for this test.
#  blender --background --factory-startup --python $HOME/background_job.py -- --text="Hello World" --render="/tmp/hello" --save="/tmp/hello.blend"
#
# Notice:
# '--factory-startup' is used to avoid the user default settings from interfearing with automated scene generation.
# '--' causes blender to ignore all following arguments so python can use them.
#
# See blender --help for details.

import bpy


def example_function(body_text, save_path, render_path):

    scene = bpy.context.scene

    # Clear existing objects.
    scene.camera = None
    for obj in scene.objects:
        scene.objects.unlink(obj)

    txt_data = bpy.data.curves.new(name="MyText", type='FONT')

    # Text Object
    txt_ob = bpy.data.objects.new(name="MyText", object_data=txt_data)
    scene.objects.link(txt_ob)            # add the data to the scene as an object
    txt_data.body = body_text                     # set the body text to the command line arg given
    txt_data.align = 'CENTER'                    # center text

    # Camera
    cam_data = bpy.data.cameras.new("MyCam")        # create new camera data
    cam_ob = bpy.data.objects.new(name="MyCam", object_data=cam_data)
    scene.objects.link(cam_ob)            # add the camera data to the scene (creating a new object)
    scene.camera = cam_ob                    # set the active camera
    cam_ob.location = 0.0, 0.0, 10.0

    # Lamp
    lamp_data = bpy.data.lamps.new("MyLamp", 'POINT')
    lamp_ob = bpy.data.objects.new(name="MyCam", object_data=lamp_data)
    scene.objects.link(lamp_ob)
    lamp_ob.location = 2.0, 2.0, 5.0

    if save_path:
        try:
            f = open(save_path, 'w')
            f.close()
            ok = True
        except:
            print("Cannot save to path %r" % save_path)

            import traceback
            traceback.print_exc()

        if ok:
            bpy.ops.wm.save_as_mainfile(filepath=save_path)

    if render_path:
        render = scene.render
        render.use_file_extension = True
        render.filepath = render_path
        bpy.ops.render.render(write_still=True)


import sys        # to get command line args
import optparse    # to parse options for us and print a nice help message


def main():

    # get the args passed to blender after "--", all of which are ignored by blender specifically
    # so python may receive its own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = "Run blender in background mode with this script:"
    usage_text += "  blender -b -P " + __file__ + " -- [options]"

    parser = optparse.OptionParser(usage=usage_text)

    # Example background utility, add some text and renders or saves it (with options)
    # Possible types are: string, int, long, choice, float and complex.
    parser.add_option("-t", "--text", dest="body_text", help="This text will be used to render an image", type="string")

    parser.add_option("-s", "--save", dest="save_path", help="Save the generated file to the specified path", metavar='FILE')
    parser.add_option("-r", "--render", dest="render_path", help="Render an image to the specified path", metavar='FILE')

    options, args = parser.parse_args(argv)  # In this example we wont use the args

    if not argv:
        parser.print_help()
        return

    if not options.body_text:
        print("Error: --text=\"some string\" argument not given, aborting.")
        parser.print_help()
        return

    # Run the example function
    example_function(options.body_text, options.save_path, options.render_path)

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()
