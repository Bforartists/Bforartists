#Starting from 1825 (stearin)

import bpy
bpy.context.object.data.type = 'POINT'
lampdata = bpy.context.object.data

lampdata.color = (1.0, 0.7176470756530762, 0.2980392277240753)
#lampdata.color = (1.0, 0.5764706134796143, 0.16078431904315948)
#http://terpconnect.umd.edu/~pbs/2011-Sunderland-et-al-PCI.pdf
#https://blog.1000bulbs.com/home/whats-the-difference-between-candela-lux-and-lumens
#Environment    Typical Lux
#Hospital Theatre   1,000
#Supermarket, Workshop, Sports Hall     750
#Office, Show Rooms, Laboratories, Kitchens     500
#Warehouse Loading Bays     300 to 400
#School Classroom, University Lecture Hall  250
#Lobbies, Public Corridors, Stairwells  200
#Warehouse Aisles   100 to 200
#Homes, Theatres    150
#Family Living Room 50
#Sunset & Sunrise   400 lux
lampdata.energy = 2.0 #two times lux value
