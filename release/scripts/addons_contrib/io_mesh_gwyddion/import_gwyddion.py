# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import os
import re
from math import pi, sqrt
from mathutils import Vector, Matrix
import struct

# All data for the images. Basically, each variable is a list with a length,
# which equals the number of images.
# Some of the variables are still not used. However, I keep them for purposes
# in future.  
class AFMData(object):
    def __init__(self, date, x_size, y_size, x_pixel, y_pixel, x_off, y_off, 
                 voltage, feedback, gain, speed, amplitude, angle, datfile, 
                 channel, unit, z_factor, spec_x_unit, spec_x_label, spec_y_unit, 
                 spec_y_label, spec_y_factor, spec_points, spec_feedback, 
                 spec_acquisition, spec_delay):
        self.date = date
        self.x_size = x_size
        self.y_size = y_size
        self.x_pixel = x_pixel
        self.y_pixel = y_pixel
        self.x_off = x_off
        self.y_off = y_off
        self.voltage = voltage
        self.feedback = feedback
        self.gain = gain
        self.speed = speed
        self.amplitude = amplitude
        self.angle = angle
        self.datfile = datfile
        self.channel = channel
        self.unit = unit
        self.z_factor = z_factor
        self.spec_x_unit = spec_x_unit    
        self.spec_x_label = spec_x_label     
        self.spec_y_unit = spec_y_unit
        self.spec_y_label = spec_y_label
        self.spec_y_factor = spec_y_factor      
        self.spec_points = spec_points
        self.spec_feedback = spec_feedback
        self.spec_acquisition = spec_acquisition
        self.spec_delay = spec_delay     
      

# For loading the Gwyddion images. I basically have followed rules described 
# here: http://gwyddion.net/documentation/user-guide-en/gwyfile-format.html
def load_gwyddion_images(data_file, channels):
   
    if not os.path.isfile(data_file):
        return False  

    AFMdata = AFMData([],[],[],[],[],[],[],
                      [],[],[],[],[],[],[],
                      [],[],[],[],[],[],[],
                      [],[],[],[],[])
    AFMdata.datfile = data_file
    
    datafile = open(data_file, 'rb')
    data = datafile.read()
    datafile.close()   
    
    # Search the title of each image
    for a in list(re.finditer(b"data/title\x00", data)):    
            
        pos = a.start()
        channel_number = int(data[pos-2:pos-1])
        
        if channels[channel_number] == False:
            continue
                
        pos1 = data[pos:].find(b"\x00") + pos + len("\x00") + 1
        pos2 = data[pos1:].find(b"\x00") + pos1

        channel_name = data[pos1:pos2].decode("utf-8")
        
        AFMdata.channel.append([channel_number, channel_name])    
        
    # Search important parameters and finally the image data.    
    images = []    
    for a in list(re.finditer(b"/data\x00", data)):
    
        pos = a.start()    

        channel_number = int(data[pos-1:pos])
        
        if channels[channel_number] == False:
            continue

        # Find the image size in pixel (x direction)
        pos1 = data[pos:].find(b"xres") + pos+len("xres")
        size_x_pixel = struct.unpack("i",data[pos1+2:pos1+4+2])[0]

        # ... the image size in pixel (y direction)
        pos1 = data[pos:].find(b"yres") + pos+len("yres")
        size_y_pixel = struct.unpack("i",data[pos1+2:pos1+4+2])[0]

        # ... the real image size (x direction)
        pos1 = data[pos:].find(b"xreal") + pos+len("xreal")
        size_x_real = struct.unpack("d",data[pos1+2:pos1+8+2])[0]

        # ... the real image size (y direction)
        pos1 = data[pos:].find(b"yreal") + pos+len("yreal")
        size_y_real = struct.unpack("d",data[pos1+2:pos1+8+2])[0]

        # If it is a z image, multiply with 10^9 nm
        factor = 1.0        
        pos1 = data[pos:].find(b"si_unit_z") + pos
        unit = data[pos1+34:pos1+36].decode("utf-8")
        if "m" in unit:
            factor = 1000000000.0
        
        # Now, find the image data and store it
        pos1 = data[pos:].find(b"\x00data\x00") + pos + len("\x00data\x00") + 5

        image = []        
        for i in range(size_y_pixel):
            line = []
            for j in range(size_x_pixel):
                # The '8' is for the double values
                k = pos1 + (i*size_x_pixel+j)   * 8
                l = pos1 + (i*size_x_pixel+j+1) * 8
                line.append(struct.unpack("d",data[k:l])[0]*factor)
            image.append(line)     
            
        images.append(image)
   
        # Note all parameters of the image.
        AFMdata.x_pixel.append(int(size_x_pixel))
        AFMdata.y_pixel.append(int(size_y_pixel))
        AFMdata.x_size.append(size_x_real * 1000000000.0)
        AFMdata.y_size.append(size_y_real * 1000000000.0)
    
    return (images, AFMdata)

# Routine to create the mesh and finally the image
def create_mesh(data_list, 
                AFMdata, 
                use_smooth, 
                scale_size,
                scale_height,
                use_camera,
                use_lamp):
    # This is for the image name.       
    path_list = AFMdata.datfile.strip('/').split('/') 

    number_img = len(data_list)
    image_x_offset_gap = 10.0 * scale_size
    image_x_all = sum(AFMdata.x_size)*scale_size 
    image_x_offset = -(image_x_all+image_x_offset_gap*(number_img-1)) / 2.0
                                
    # For each image do:
    for k, data in enumerate(data_list):
      
        size_x = AFMdata.x_pixel[k]
        size_y = AFMdata.y_pixel[k]
        
        image_scale = AFMdata.x_size[k] / float(AFMdata.x_pixel[k])    
        image_scale = image_scale * scale_size    
        image_x_size = AFMdata.x_size[k] * scale_size        
        image_x_offset += image_x_size / 2.0
      
        image_name = path_list[-1] + "_" + AFMdata.channel[k][1]
        
        data_mesh = []
        data_faces = []

        #print("passed - create_mesh ---- 1")

        for i, line in enumerate(data):
            for j, pixel in enumerate(line):
            
               # The vertices
               data_mesh.append(Vector((float(i) * image_scale, 
                                        float(j) * image_scale, 
                                        float(pixel)*scale_height)))
               
               # The faces
               if i < size_y-1 and j < size_x-1:
                   data_faces.append( [size_x*i+j      , size_x*(i+1)+j, 
                                       size_x*(i+1)+j+1, size_x*i+j+1    ]) 

        #print("passed - create_mesh ---- 2")
               
        # Build the mesh
        surface_mesh = bpy.data.meshes.new("Mesh")
        surface_mesh.from_pydata(data_mesh, [], data_faces)
        surface_mesh.update()
        surface = bpy.data.objects.new(image_name, surface_mesh)
        bpy.context.scene.objects.link(surface)
        bpy.ops.object.select_all(action='DESELECT')        
        surface.select = True 

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        # sum((v.co for v in mesh.vertices), Vector()) / len(mesh.vertices)

        if use_smooth:
            for polygon in surface.data.polygons:
                polygon.use_smooth = True

        surface.location = Vector((0.0, image_x_offset, 0.0)) 
        image_x_offset += image_x_size / 2.0 + image_x_offset_gap

        #print("passed - create_mesh ---- 3")


        
    object_center_vec = Vector((0.0,0.0,0.0))
    object_size = (sum(AFMdata.x_size) * scale_size 
                   +image_x_offset_gap * (len(data_list)-1))

    # ------------------------------------------------------------------------
    # CAMERA AND LAMP
    camera_factor = 20.0
    
    # If chosen a camera is put into the scene.
    if use_camera == True:

        # Assume that the object is put into the global origin. Then, the
        # camera is moved in x and z direction, not in y. The object has its
        # size at distance sqrt(object_size) from the origin. So, move the
        # camera by this distance times a factor of camera_factor in x and z.
        # Then add x, y and z of the origin of the object.
        object_camera_vec = Vector((sqrt(object_size) * camera_factor,
                                    0.0,
                                    sqrt(object_size) * camera_factor))
        camera_xyz_vec = object_center_vec + object_camera_vec

        # Create the camera
        current_layers=bpy.context.scene.layers 
        camera_data = bpy.data.cameras.new("A_camera")
        camera_data.lens = 45
        camera_data.clip_end = 50000.0
        camera = bpy.data.objects.new("A_camera", camera_data)
        camera.location = camera_xyz_vec
        camera.layers = current_layers
        bpy.context.scene.objects.link(camera) 

        # Here the camera is rotated such it looks towards the center of
        # the object. The [0.0, 0.0, 1.0] vector along the z axis
        z_axis_vec             = Vector((0.0, 0.0, 1.0))
        # The angle between the last two vectors
        angle                  = object_camera_vec.angle(z_axis_vec, 0)
        # The cross-product of z_axis_vec and object_camera_vec
        axis_vec               = z_axis_vec.cross(object_camera_vec)
        # Rotate 'axis_vec' by 'angle' and convert this to euler parameters.
        # 4 is the size of the matrix.
        camera.rotation_euler  = Matrix.Rotation(angle, 4, axis_vec).to_euler()

        # Rotate the camera around its axis by 90° such that we have a nice
        # camera position and view onto the object.
        bpy.ops.object.select_all(action='DESELECT')        
        camera.select = True         
        bpy.ops.transform.rotate(value=(90.0*2*pi/360.0),
                                 axis=object_camera_vec,
                                 constraint_axis=(False, False, False),
                                 constraint_orientation='GLOBAL',
                                 mirror=False, proportional='DISABLED',
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1, snap=False,
                                 snap_target='CLOSEST', snap_point=(0, 0, 0),
                                 snap_align=False, snap_normal=(0, 0, 0),
                                 release_confirm=False)

    # Here a lamp is put into the scene, if chosen.
    if use_lamp == True:

        # This is the distance from the object measured in terms of %
        # of the camera distance. It is set onto 50% (1/2) distance.
        lamp_dl = sqrt(object_size) * 15 * 0.5
        # This is a factor to which extend the lamp shall go to the right
        # (from the camera  point of view).
        lamp_dy_right = lamp_dl * (3.0/4.0)

        # Create x, y and z for the lamp.
        object_lamp_vec = Vector((lamp_dl,lamp_dy_right,lamp_dl))
        lamp_xyz_vec = object_center_vec + object_lamp_vec

        # Create the lamp
        current_layers=bpy.context.scene.layers
        lamp_data = bpy.data.lamps.new(name="A_lamp", type="POINT")
        lamp_data.distance = 5000.0
        lamp_data.energy = 3.0
        lamp_data.shadow_method = 'RAY_SHADOW'        
        lamp = bpy.data.objects.new("A_lamp", lamp_data)
        lamp.location = lamp_xyz_vec
        lamp.layers = current_layers
        bpy.context.scene.objects.link(lamp)         

        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.1      
