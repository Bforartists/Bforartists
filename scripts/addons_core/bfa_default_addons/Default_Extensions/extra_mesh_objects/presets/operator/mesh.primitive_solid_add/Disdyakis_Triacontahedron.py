import bpy
op = bpy.context.active_operator

op.source = "20"
op.vTrunc = 0.921
op.eTrunc = 0.553
op.dual = 1
op.snub = "None"