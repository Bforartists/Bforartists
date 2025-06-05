#(1700K) 135W Low Pressure Sodium Vapor Starting from 1932
#Mostly used for Outdoor city lighting, security lighting, long tunnel lighting

import bpy
bpy.context.object.data.type = 'POINT'
lampdata = bpy.context.object.data

lampdata.color = (1.0, 0.5764706134796143, 0.16078431904315948)
lampdata.energy = 8.43048#22600lm/21.446(=lux)*0.004(distance) *2 for distance is the point of half strength
