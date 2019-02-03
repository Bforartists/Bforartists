import bpy
import os

# ---------------------------BATCH MAKER------------------


def batchMaker(BIN):

    if os.name == "nt":
        print("PLATFORM: WINDOWS")
        SYSBAR = os.sep
        EXTSYS = ".bat"
        QUOTES = '"'
    else:
        print("PLATFORM:LINUX")
        SYSBAR = os.sep
        EXTSYS = ".sh"
        QUOTES = ''

    FILENAME = bpy.data.filepath.rpartition(SYSBAR)[-1].rpartition(".")[0]
    BINDIR = bpy.app[4]
    SHFILE = os.path.join(
        bpy.data.filepath.rpartition(SYSBAR)[0],
        FILENAME + EXTSYS)

    renpath = bpy.context.scene.render.filepath

    with open(SHFILE, "w") as FILE:
        if not BIN:
            FILE.writelines(r"'%s' -b '%s' --python-text Text -a" % (bpy.app.binary_path,bpy.data.filepath))
        else:
            FILE.writelines(r"blender -b '%s' --python-text Text -a" % (bpy.data.filepath))
            
            

class oscBatchMaker (bpy.types.Operator):
    """It creates .bat(win) or .sh(unix) file, to execute and render from Console/Terminal"""
    bl_idname = "file.create_batch_maker_osc"
    bl_label = "Make render batch"
    bl_options = {'REGISTER', 'UNDO'}

    bin : bpy.props.BoolProperty(
        default=False,
        name="Use Environment Variable")

    def execute(self, context):
        batchMaker(self.bin)
        return {'FINISHED'}

