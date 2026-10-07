import bpy
op = bpy.context.active_operator

op.source = "8"
op.vTrunc = 2 / 3
op.eTrunc = 0
op.dual = 1
op.snub = "None"