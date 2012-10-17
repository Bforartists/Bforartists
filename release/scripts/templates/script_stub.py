# This stub runs a python script relative to the currently open
# blend file, useful when editing scripts externally.

import bpy
import os

# Use your own script name here:
filename = "my_script.py"

filepath = os.path.join(os.path.basename(bpy.data.filepath), filename)
exec(compile(open(filepath).read(), filepath, 'exec'))
