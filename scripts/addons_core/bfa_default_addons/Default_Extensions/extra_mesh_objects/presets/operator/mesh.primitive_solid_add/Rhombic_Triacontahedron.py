import bpy
op = bpy.context.active_operator

op.source = "12"
op.vTrunc = 1
op.eTrunc = 0
op.dual = 1
op.snub = "None"