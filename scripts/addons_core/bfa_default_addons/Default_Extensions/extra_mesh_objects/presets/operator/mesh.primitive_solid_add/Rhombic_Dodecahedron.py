import bpy
op = bpy.context.active_operator

op.source = "4"
op.vTrunc = 1
op.eTrunc = 1
op.dual = 1
op.snub = "None"