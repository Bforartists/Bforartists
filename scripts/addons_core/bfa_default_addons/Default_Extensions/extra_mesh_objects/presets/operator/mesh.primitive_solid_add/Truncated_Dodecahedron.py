import bpy
op = bpy.context.active_operator

op.source = "12"
op.vTrunc = 2 / 3
op.eTrunc = 0
op.dual = 0
op.snub = "None"