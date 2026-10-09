import bpy
op = bpy.context.active_operator

op.source = "12"
op.vTrunc = 1.1235
op.eTrunc = 0.68
op.dual = 1
op.snub = "Left"