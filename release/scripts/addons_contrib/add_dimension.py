# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and / or
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

bl_info = {
    'name': 'Dimension',
    'author': 'Spivak Vladimir (http://cwolf3d.korostyshev.net)',
    'version': (3, 9, 5),
    'blender': (2, 7, 8),
    'location': 'View3D > Add > Curve',
    'description': 'Adds Dimension',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Curve/Dimension',
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    'category': 'Add Curve'}


##------------------------------------------------------------
#### import modules
import bpy
from bpy.props import  *
from mathutils import  *
from math import  *
from bpy.app.handlers import persistent

# Add a TextCurve
def addText(string = '', loc = ((0, 0, 0)), textsize = 1, align = 'CENTER', offset_y = 0, font = ''):

    tcu = bpy.data.curves.new(string + 'Data', 'FONT')
    text = bpy.data.objects.new(string + 'Text', tcu)
    tcu.body = string
    tcu.align_x = align
    tcu.size = textsize
    tcu.offset_y = offset_y
    if font == '':
        fnt = bpy.data.fonts[0]
    else:
        fnt = bpy.data.fonts.load(font)
    tcu.font = fnt
    text.location = loc
    bpy.context.scene.objects.link(text)

    return text

##------------------------------------------------------------
# Dimension: Linear-1
def Linear1(width = 2, length = 2, dsize = 1, depth = 0.1, center = False, arrow = 'Arrow1', arrowdepth = 0.1, arrowlength = 0.25):

    newpoints = []

    w = 1
    if width < 0:
        w = -1
    l = 1
    if length < 0:
        l = -1

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    if arrow == 'Arrow1' or arrow == 'Arrow2':
        newpoints.append([-center1, 0, 0]) #1
        newpoints.append([-center1, length, 0]) #2
        newpoints.append([-center1, length + l * dsize, 0]) #3
        newpoints.append([center2, length + l * dsize, 0]) #4
        newpoints.append([center2, length + l * dsize / 2 + l * depth / 100, 0]) #5
        newpoints.append([center2 + w * arrowlength, length + l * dsize / 2 + l * arrowdepth + l * depth / 2, 0]) #6
        if arrow == 'Arrow1':
            newpoints.append([center2 + w * arrowlength, length + l * dsize / 2 + l * depth / 2, 0]) #7
            newpoints.append([width-center2-w * arrowlength, length + l * dsize / 2 + l * depth / 2, 0]) #8
        else:
            newpoints.append([center2 + w * arrowlength * 3 / 4, length + l * dsize / 2 + l * depth / 2, 0]) #7
            newpoints.append([width-center2-w * arrowlength * 3 / 4, length + l * dsize / 2 + l * depth / 2, 0]) #8
        newpoints.append([width-center2-w * arrowlength, length + l * dsize / 2 + l * arrowdepth + l * depth / 2, 0]) #9
        newpoints.append([width-center2, length + l * dsize / 2 + l * depth / 100, 0]) #10
        newpoints.append([width-center2, length + l * dsize, 0]) #11
        newpoints.append([width + center1, length + l * dsize, 0]) #12
        newpoints.append([width + center1, length, 0]) #13
        newpoints.append([width + center1, 0, 0]) #14
        newpoints.append([width-center2, 0, 0]) #15
        newpoints.append([width-center2, length, 0]) #16
        newpoints.append([width-center2, length + l * dsize / 2-l * depth / 100, 0]) #17
        newpoints.append([width-center2-w * arrowlength, length + l * dsize / 2-l * arrowdepth-l * depth / 2, 0]) #18
        if arrow == 'Arrow1':
            newpoints.append([width-center2-w * arrowlength, length + l * dsize / 2-l * depth / 2, 0]) #19
            newpoints.append([center2 + w * arrowlength, length + l * dsize / 2-l * depth / 2, 0]) #20
        else:
            newpoints.append([width-center2-w * arrowlength * 3 / 4, length + l * dsize / 2-l * depth / 2, 0]) #19
            newpoints.append([center2 + w * arrowlength * 3 / 4, length + l * dsize / 2-l * depth / 2, 0]) #20
        newpoints.append([center2 + w * arrowlength, length + l * dsize / 2-l * arrowdepth-l * depth / 2, 0]) #21
        newpoints.append([center2, length + l * dsize / 2-l * depth / 100, 0]) #22
        newpoints.append([center2, length, 0]) #23
        newpoints.append([center2, 0, 0]) #24

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        b = sqrt(depth * depth / 2)
        x = sin(radians(45)) * arrowlength * w
        y = cos(radians(45)) * arrowlength * l
        newpoints.append([-center1, 0, 0]) #1
        newpoints.append([-center1, length, 0]) #2
        newpoints.append([-center1, length + l * dsize / 2-l * depth / 2-l * b, 0]) #3
        newpoints.append([-center1-x, length + l * dsize / 2-l * depth / 2-l * b-y, 0]) #4
        newpoints.append([-center1-w * b-x, length + l * dsize / 2-l * depth / 2-y, 0]) #5
        if arrow == 'Serifs2':
            newpoints.append([-center1-w * b, length + l * dsize / 2-l * depth / 2, 0]) #6
            newpoints.append([-center1-w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #7
            newpoints.append([-center1-w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #8
        newpoints.append([-center1, length + l * dsize / 2 + l * depth / 2, 0]) #9
        newpoints.append([-center1, length + l * dsize, 0]) #10
        newpoints.append([center2, length + l * dsize, 0]) #11
        newpoints.append([center2, length + l * dsize / 2 + l * depth / 2 + l * b, 0]) #12
        newpoints.append([center2 + x, length + l * dsize / 2 + l * depth / 2 + l * b + y, 0]) #13
        newpoints.append([center2 + w * b + x, length + l * dsize / 2 + l * depth / 2 + y, 0]) #14
        newpoints.append([center2 + w * b, length + l * dsize / 2 + l * depth / 2, 0]) #15
        newpoints.append([width-center2, length + l * dsize / 2 + l * depth / 2, 0]) #16
        newpoints.append([width-center2, length + l * dsize, 0]) #17
        newpoints.append([width + center1, length + l * dsize, 0]) #18
        newpoints.append([width + center1, length + l * dsize / 2 + l * depth / 2 + l * b, 0]) #19
        newpoints.append([width + center1 + x, length + l * dsize / 2 + l * depth / 2 + l * b + y, 0]) #20
        newpoints.append([width + center1 + w * b + x, length + l * dsize / 2 + l * depth / 2 + y, 0]) #21
        if arrow == 'Serifs2':
            newpoints.append([width + center1 + w * b, length + l * dsize / 2 + l * depth / 2, 0]) #22
            newpoints.append([width + center1 + w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #23
            newpoints.append([width + center1 + w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #24
        newpoints.append([width + center1, length + l * dsize / 2-l * depth / 2, 0]) #25
        newpoints.append([width + center1, length, 0]) #26
        newpoints.append([width + center1, 0, 0]) #27
        newpoints.append([width-center2, 0, 0]) #28
        newpoints.append([width-center2, length, 0]) #29
        newpoints.append([width-center2, length + l * dsize / 2-l * depth / 2-l * b, 0]) #30
        newpoints.append([width-center2-x, length + l * dsize / 2-l * depth / 2-l * b-y, 0]) #31
        newpoints.append([width-center2-w * b-x, length + l * dsize / 2-l * depth / 2-y, 0]) #32
        newpoints.append([width-center2-w * b, length + l * dsize / 2-l * depth / 2, 0]) #33
        newpoints.append([center2, length + l * dsize / 2-l * depth / 2, 0]) #34
        newpoints.append([center2, length, 0]) #35
        newpoints.append([center2, 0, 0]) #36

    if arrow == 'Without':
        newpoints.append([-center1, 0, 0]) #1
        newpoints.append([-center1, length, 0]) #2
        newpoints.append([-center1, length + l * dsize, 0]) #3
        newpoints.append([center2, length + l * dsize, 0]) #4
        newpoints.append([center2, length + l * dsize / 2 + l * depth / 2, 0]) #7
        newpoints.append([width-center2, length + l * dsize / 2 + l * depth / 2, 0]) #8
        newpoints.append([width-center2, length + l * dsize, 0]) #11
        newpoints.append([width + center1, length + l * dsize, 0]) #12
        newpoints.append([width + center1, length, 0]) #13
        newpoints.append([width + center1, 0, 0]) #14
        newpoints.append([width-center2, 0, 0]) #15
        newpoints.append([width-center2, length, 0]) #16
        newpoints.append([width-center2, length + l * dsize / 2-l * depth / 2, 0]) #19
        newpoints.append([center2, length + l * dsize / 2-l * depth / 2, 0]) #20
        newpoints.append([center2, length, 0]) #23
        newpoints.append([center2, 0, 0]) #24

    return newpoints

##------------------------------------------------------------
# Dimension: Linear-2
def Linear2(width = 2, dsize = 1, depth = 0.1, center = False, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    w = 1
    if width < 0:
        w = -1

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    if arrow == 'Arrow1' or arrow == 'Arrow2':
        newpoints.append([0, 0, 0]) #1
        newpoints.append([w * arrowlength, arrowdepth + depth / 2, 0]) #2
        if arrow == 'Arrow1':
            newpoints.append([w * arrowlength, depth / 2, 0]) #3
            newpoints.append([width-w * arrowlength, depth / 2, 0]) #4
        else:
            newpoints.append([w * arrowlength * 3 / 4, depth / 2, 0]) #3
            newpoints.append([width-w * arrowlength * 3 / 4, depth / 2, 0]) #4
        newpoints.append([width-w * arrowlength, arrowdepth + depth / 2, 0]) #5
        newpoints.append([width, 0, 0]) #6
        newpoints.append([width-w * arrowlength, -arrowdepth-depth / 2, 0]) #7
        if arrow == 'Arrow1':
            newpoints.append([width-w * arrowlength, -depth / 2, 0]) #8
            newpoints.append([w * arrowlength, -depth / 2, 0]) #9
        else:
            newpoints.append([width-w * arrowlength * 3 / 4, -depth / 2, 0]) #8
            newpoints.append([w * arrowlength * 3 / 4, -depth / 2, 0]) #9
        newpoints.append([w * arrowlength, -arrowdepth-depth / 2, 0]) #10

    if arrow == 'Serifs1':
        b = sqrt(depth * depth / 2)
        x = sin(radians(45)) * arrowlength * w
        y = cos(radians(45)) * arrowlength
        newpoints.append([-center1, -dsize / 2, 0]) #2
        newpoints.append([-center1, -depth / 2-b, 0]) #3
        newpoints.append([-center1-x, -depth / 2-b-y, 0]) #4
        newpoints.append([-center1-w * b-x, -depth / 2-y, 0]) #5
        newpoints.append([-center1-w * b, -depth / 2, 0]) #6
        newpoints.append([-center1-w * dsize / 2, -depth / 2, 0]) #7
        newpoints.append([-center1-w * dsize / 2, depth / 2, 0]) #8
        newpoints.append([-center1, depth / 2, 0]) #9
        newpoints.append([-center1, dsize / 2, 0]) #10
        newpoints.append([center2, dsize / 2, 0]) #11
        newpoints.append([center2, depth / 2 + b, 0]) #12
        newpoints.append([center2 + x, depth / 2 + b + y, 0]) #13
        newpoints.append([center2 + w * b + x, depth / 2 + y, 0]) #14
        newpoints.append([center2 + w * b, depth / 2, 0]) #15
        newpoints.append([width-center2, depth / 2, 0]) #16
        newpoints.append([width-center2, dsize / 2, 0]) #17
        newpoints.append([width + center1, dsize / 2, 0]) #18
        newpoints.append([width + center1, depth / 2 + b, 0]) #19
        newpoints.append([width + center1 + x, depth / 2 + b + y, 0]) #20
        newpoints.append([width + center1 + w * b + x, depth / 2 + y, 0]) #21
        newpoints.append([width + center1 + w * b, depth / 2, 0]) #22
        newpoints.append([width + center1 + w * dsize / 2, depth / 2, 0]) #23
        newpoints.append([width + center1 + w * dsize / 2, -depth / 2, 0]) #24
        newpoints.append([width + center1, -depth / 2, 0]) #25
        newpoints.append([width + center1, -dsize / 2, 0]) #26
        newpoints.append([width-center2, -dsize / 2, 0]) #29
        newpoints.append([width-center2, -depth / 2-b, 0]) #30
        newpoints.append([width-center2-x, -depth / 2-b-y, 0]) #31
        newpoints.append([width-center2-w * b-x, -depth / 2-y, 0]) #32
        newpoints.append([width-center2-w * b, -depth / 2, 0]) #33
        newpoints.append([center2, -depth / 2, 0]) #34
        newpoints.append([center2, -dsize / 2, 0]) #35

    if arrow == 'Serifs2':
        b = sqrt(depth * depth / 2)
        x = sin(radians(45)) * arrowlength * w
        y = cos(radians(45)) * arrowlength
        newpoints.append([-center1 + w * b, -depth / 2, 0]) #3
        newpoints.append([-center1-x, -depth / 2-b-y, 0]) #4
        newpoints.append([-center1-w * b-x, -depth / 2-y, 0]) #5
        newpoints.append([center2 + x, depth / 2 + b + y, 0]) #13
        newpoints.append([center2 + w * b + x, depth / 2 + y, 0]) #14
        newpoints.append([center2 + w * b, depth / 2, 0]) #15
        newpoints.append([width + center1-w * b, depth / 2, 0]) #19
        newpoints.append([width + center1 + x, depth / 2 + b + y, 0]) #20
        newpoints.append([width + center1 + w * b + x, depth / 2 + y, 0]) #21
        newpoints.append([width-center2-x, -depth / 2-b-y, 0]) #31
        newpoints.append([width-center2-w * b-x, -depth / 2-y, 0]) #32
        newpoints.append([width-center2-w * b, -depth / 2, 0]) #33

    if arrow == 'Without':
        newpoints.append([0, depth / 2, 0]) #3
        newpoints.append([width, depth / 2, 0]) #4
        newpoints.append([width, -depth / 2, 0]) #8
        newpoints.append([0, -depth / 2, 0]) #9

    return newpoints

##------------------------------------------------------------
# Dimension: Linear-3
def Linear3(width = 2, length = 2, dsize = 1, depth = 0.1, center = False, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    w = 1
    if width < 0:
        w = -1
    l = 1
    if length < 0:
        l = -1

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    if arrow == 'Arrow1' or arrow == 'Arrow2':
        newpoints.append([-center1, 0, 0]) #1
        newpoints.append([-center1, length, 0]) #2
        newpoints.append([-center1, length + l * dsize / 2-l * depth / 100, 0]) #3
        newpoints.append([-center1-w * arrowlength, length + l * dsize / 2-l * arrowdepth-l * depth / 2, 0]) #4
        if arrow == 'Arrow1':
            newpoints.append([-center1-w * arrowlength, length + l * dsize / 2-l * depth / 2, 0]) #5
        else:
            newpoints.append([-center1-w * arrowlength * 3 / 4, length + l * dsize / 2-l * depth / 2, 0]) #5
        newpoints.append([-center1-w * arrowlength-w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #6
        newpoints.append([-center1-w * arrowlength-w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #7
        if arrow == 'Arrow1':
            newpoints.append([-center1-w * arrowlength, length + l * dsize / 2 + l * depth / 2, 0]) #8
        else:
            newpoints.append([-center1-w * arrowlength * 3 / 4, length + l * dsize / 2 + l * depth / 2, 0]) #8
        newpoints.append([-center1-w * arrowlength, length + l * dsize / 2 + l * arrowdepth + l * depth / 2, 0]) #9
        newpoints.append([-center1, length + l * dsize / 2 + l * depth / 100, 0]) #10
        newpoints.append([-center1, length + l * dsize, 0]) #11
        newpoints.append([center2, length + l * dsize, 0]) #12
        newpoints.append([center2, length + l * dsize / 2 + l * depth / 2, 0]) #13
        newpoints.append([width-center2, length + l * dsize / 2 + l * depth / 2, 0]) #14
        newpoints.append([width-center2, length + l * dsize, 0]) #15
        newpoints.append([width + center1, length + l * dsize, 0]) #16
        newpoints.append([width + center1, length + l * dsize / 2 + l * depth / 100, 0]) #17
        newpoints.append([width + center1 + w * arrowlength, length + l * dsize / 2 + l * arrowdepth + l * depth / 2, 0]) #18
        if arrow == 'Arrow1':
            newpoints.append([width + center1 + w * arrowlength, length + l * dsize / 2 + l * depth / 2, 0]) #19
        else:
            newpoints.append([width + center1 + w * arrowlength * 3 / 4, length + l * dsize / 2 + l * depth / 2, 0]) #19
        newpoints.append([width + center1 + w * arrowlength + w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #20
        newpoints.append([width + center1 + w * arrowlength + w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #21
        if arrow == 'Arrow1':
            newpoints.append([width + center1 + w * arrowlength, length + l * dsize / 2-l * depth / 2, 0]) #22
        else:
            newpoints.append([width + center1 + w * arrowlength * 3 / 4, length + l * dsize / 2-l * depth / 2, 0]) #22
        newpoints.append([width + center1 + w * arrowlength, length + l * dsize / 2-l * arrowdepth-l * depth / 2, 0]) #23
        newpoints.append([width + center1, length + l * dsize / 2-l * depth / 100, 0]) #24
        newpoints.append([width + center1, length, 0]) #25
        newpoints.append([width + center1, 0, 0]) #26
        newpoints.append([width-center2, 0, 0]) #27
        newpoints.append([width-center2, length, 0]) #28
        newpoints.append([width-center2, length + l * dsize / 2-l * depth / 2, 0]) #29
        newpoints.append([center2, length + l * dsize / 2-l * depth / 2, 0]) #30
        newpoints.append([center2, length, 0]) #31
        newpoints.append([center2, 0, 0]) #32

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        b = sqrt(depth * depth / 2)
        x = sin(radians(45)) * arrowlength * w
        y = cos(radians(45)) * arrowlength * l
        newpoints.append([-center1, 0, 0]) #1
        newpoints.append([-center1, length, 0]) #2
        newpoints.append([-center1, length + l * dsize / 2-l * depth / 2-l * b, 0]) #3
        newpoints.append([-center1-x, length + l * dsize / 2-l * depth / 2-l * b-y, 0]) #4
        newpoints.append([-center1-w * b-x, length + l * dsize / 2-l * depth / 2-y, 0]) #5
        newpoints.append([-center1-w * b, length + l * dsize / 2-l * depth / 2, 0]) #6
        if arrow == 'Serifs1':
            newpoints.append([-center1-w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #7
            newpoints.append([-center1-w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #8
        else:
            newpoints.append([-center1-w * dsize, length + l * dsize / 2-l * depth / 2, 0]) #7
            newpoints.append([-center1-w * dsize, length + l * dsize / 2 + l * depth / 2, 0]) #8
        newpoints.append([-center1, length + l * dsize / 2 + l * depth / 2, 0]) #9
        newpoints.append([-center1, length + l * dsize, 0]) #10
        newpoints.append([center2, length + l * dsize, 0]) #11
        newpoints.append([center2, length + l * dsize / 2 + l * depth / 2 + l * b, 0]) #12
        newpoints.append([center2 + x, length + l * dsize / 2 + l * depth / 2 + l * b + y, 0]) #13
        newpoints.append([center2 + w * b + x, length + l * dsize / 2 + l * depth / 2 + y, 0]) #14
        newpoints.append([center2 + w * b, length + l * dsize / 2 + l * depth / 2, 0]) #15
        newpoints.append([width-center2, length + l * dsize / 2 + l * depth / 2, 0]) #16
        newpoints.append([width-center2, length + l * dsize, 0]) #17
        newpoints.append([width + center1, length + l * dsize, 0]) #18
        newpoints.append([width + center1, length + l * dsize / 2 + l * depth / 2 + l * b, 0]) #19
        newpoints.append([width + center1 + x, length + l * dsize / 2 + l * depth / 2 + l * b + y, 0]) #20
        newpoints.append([width + center1 + w * b + x, length + l * dsize / 2 + l * depth / 2 + y, 0]) #21
        newpoints.append([width + center1 + w * b, length + l * dsize / 2 + l * depth / 2, 0]) #22
        if arrow == 'Serifs1':
            newpoints.append([width + center1 + w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #23
            newpoints.append([width + center1 + w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #24
        else:
            newpoints.append([width + center1 + w * dsize, length + l * dsize / 2 + l * depth / 2, 0]) #23
            newpoints.append([width + center1 + w * dsize, length + l * dsize / 2-l * depth / 2, 0]) #24
        newpoints.append([width + center1, length + l * dsize / 2-l * depth / 2, 0]) #25
        newpoints.append([width + center1, length, 0]) #26
        newpoints.append([width + center1, 0, 0]) #27
        newpoints.append([width-center2, 0, 0]) #28
        newpoints.append([width-center2, length, 0]) #29
        newpoints.append([width-center2, length + l * dsize / 2-l * depth / 2-l * b, 0]) #30
        newpoints.append([width-center2-x, length + l * dsize / 2-l * depth / 2-l * b-y, 0]) #31
        newpoints.append([width-center2-w * b-x, length + l * dsize / 2-l * depth / 2-y, 0]) #32
        newpoints.append([width-center2-w * b, length + l * dsize / 2-l * depth / 2, 0]) #33
        newpoints.append([center2, length + l * dsize / 2-l * depth / 2, 0]) #34
        newpoints.append([center2, length, 0]) #35
        newpoints.append([center2, 0, 0]) #36

    if arrow == 'Without':
        newpoints.append([-center1, 0, 0]) #1
        newpoints.append([-center1, length, 0]) #2
        newpoints.append([-center1, length + l * dsize / 2-l * depth / 2, 0]) #5
        newpoints.append([-center1-w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #6
        newpoints.append([-center1-w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #7
        newpoints.append([-center1, length + l * dsize / 2 + l * depth / 2, 0]) #8
        newpoints.append([-center1, length + l * dsize, 0]) #11
        newpoints.append([center2, length + l * dsize, 0]) #12
        newpoints.append([center2, length + l * dsize / 2 + l * depth / 2, 0]) #13
        newpoints.append([width-center2, length + l * dsize / 2 + l * depth / 2, 0]) #14
        newpoints.append([width-center2, length + l * dsize, 0]) #15
        newpoints.append([width + center1, length + l * dsize, 0]) #16
        newpoints.append([width + center1, length + l * dsize / 2 + l * depth / 2, 0]) #19
        newpoints.append([width + center1 + w * dsize / 2, length + l * dsize / 2 + l * depth / 2, 0]) #20
        newpoints.append([width + center1 + w * dsize / 2, length + l * dsize / 2-l * depth / 2, 0]) #21
        newpoints.append([width + center1, length + l * dsize / 2-l * depth / 2, 0]) #22
        newpoints.append([width + center1, length, 0]) #25
        newpoints.append([width + center1, 0, 0]) #26
        newpoints.append([width-center2, 0, 0]) #27
        newpoints.append([width-center2, length, 0]) #28
        newpoints.append([width-center2, length + l * dsize / 2-l * depth / 2, 0]) #29
        newpoints.append([center2, length + l * dsize / 2-l * depth / 2, 0]) #30
        newpoints.append([center2, length, 0]) #31
        newpoints.append([center2, 0, 0]) #32

    return newpoints

##------------------------------------------------------------
# Dimension: Radius
def Radius(width = 2, length = 2, dsize = 1, depth = 0.1, center = False, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    w = 1
    if width < 0:
        w = -1
    length = abs(length)

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    if arrow == 'Arrow1' or arrow == 'Arrow2':
        newpoints.append([0, depth / 2, 0]) #1
        newpoints.append([width, depth / 2, 0]) #2
        newpoints.append([width + w * arrowlength, depth / 2 + arrowdepth, 0]) #3
        if arrow == 'Arrow1':
            newpoints.append([width + w * arrowlength, depth / 2, 0]) #4
        else:
            newpoints.append([width + w * arrowlength * 3 / 4, depth / 2, 0]) #4
        newpoints.append([width + w * arrowlength + w * length, depth / 2, 0]) #5
        newpoints.append([width + w * arrowlength + w * length, -depth / 2, 0]) #6
        if arrow == 'Arrow1':
            newpoints.append([width + w * arrowlength, -depth / 2, 0]) #7
        else:
            newpoints.append([width + w * arrowlength * 3 / 4, -depth / 2, 0]) #7
        newpoints.append([width + w * arrowlength, -depth / 2-arrowdepth, 0]) #8
        newpoints.append([width, -depth / 2, 0]) #9
        newpoints.append([0, -depth / 2, 0]) #10

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        b = sqrt(depth * depth / 2)
        x = sin(radians(45)) * arrowlength * w
        y = cos(radians(45)) * arrowlength
        newpoints.append([0, depth / 2, 0]) #1
        if arrow == 'Serifs1':
            newpoints.append([width-center2, depth / 2, 0]) #16
            newpoints.append([width-center2, dsize / 2, 0]) #17
            newpoints.append([width + center1, dsize / 2, 0]) #18
            newpoints.append([width + center1, depth / 2 + b, 0]) #19
        else:
            newpoints.append([width + center1-w * b, depth / 2, 0]) #19
        newpoints.append([width + center1 + x, depth / 2 + b + y, 0]) #20
        newpoints.append([width + center1 + w * b + x, depth / 2 + y, 0]) #21
        newpoints.append([width + center1 + w * b, depth / 2, 0]) #22
        newpoints.append([width + center1 + w * length, depth / 2, 0]) #23
        newpoints.append([width + center1 + w * length, -depth / 2, 0]) #24
        if arrow == 'Serifs1':
            newpoints.append([width + center1, -depth / 2, 0]) #25
            newpoints.append([width + center1, -dsize / 2, 0]) #26
            newpoints.append([width-center2, -dsize / 2, 0]) #29
            newpoints.append([width-center2, -depth / 2-b, 0]) #30
        else:
            newpoints.append([width-center2 + w * b, -depth / 2, 0]) #30
        newpoints.append([width-center2-x, -depth / 2-b-y, 0]) #31
        newpoints.append([width-center2-w * b-x, -depth / 2-y, 0]) #32
        newpoints.append([width-center2-w * b, -depth / 2, 0]) #33
        newpoints.append([0, -depth / 2, 0]) #10

    if arrow == 'Without':
        newpoints.append([0, depth / 2, 0]) #1
        newpoints.append([width, depth / 2, 0]) #2
        newpoints.append([width, -depth / 2, 0]) #9
        newpoints.append([0, -depth / 2, 0]) #10

    return newpoints

##------------------------------------------------------------
# Dimension: Diameter
def Diameter(width = 2, length = 2, dsize = 1, depth = 0.1, center = False, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    width = width / 2
    w = 1
    if width < 0:
        w = -1
    length = abs(length)

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    if arrow == 'Arrow1' or arrow == 'Arrow2':
        newpoints.append([0, depth / 2, 0]) #1
        newpoints.append([width, depth / 2, 0]) #2
        newpoints.append([width + w * arrowlength, depth / 2 + arrowdepth, 0]) #3
        if arrow == 'Arrow1':
            newpoints.append([width + w * arrowlength, depth / 2, 0]) #4
        else:
            newpoints.append([width + w * arrowlength * 3 / 4, depth / 2, 0]) #4
        newpoints.append([width + w * arrowlength + w * length, depth / 2, 0]) #5
        newpoints.append([width + w * arrowlength + w * length, -depth / 2, 0]) #6
        if arrow == 'Arrow1':
            newpoints.append([width + w * arrowlength, -depth / 2, 0]) #7
        else:
            newpoints.append([width + w * arrowlength * 3 / 4, -depth / 2, 0]) #7
        newpoints.append([width + w * arrowlength, -depth / 2-arrowdepth, 0]) #8
        newpoints.append([width, -depth / 2, 0]) #9
        newpoints.append([0, -depth / 2, 0]) #10
        newpoints.append([-width, -depth / 2, 0]) #11
        newpoints.append([-width-w * arrowlength, -depth / 2-arrowdepth, 0]) #12
        if arrow == 'Arrow1':
            newpoints.append([-width-w * arrowlength, -depth / 2, 0]) #13
        else:
            newpoints.append([-width-w * arrowlength * 3 / 4, -depth / 2, 0]) #13
        newpoints.append([-width-w * arrowlength-w * length, -depth / 2, 0]) #14
        newpoints.append([-width-w * arrowlength-w * length, depth / 2, 0]) #15
        if arrow == 'Arrow1':
            newpoints.append([-width-w * arrowlength, depth / 2, 0]) #16
        else:
            newpoints.append([-width-w * arrowlength * 3 / 4, depth / 2, 0]) #16
        newpoints.append([-width-w * arrowlength, depth / 2 + arrowdepth, 0]) #17
        newpoints.append([-width, depth / 2, 0]) #18

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        b = sqrt(depth * depth / 2)
        x = sin(radians(45)) * arrowlength * w
        y = cos(radians(45)) * arrowlength
        newpoints.append([0, depth / 2, 0]) #1
        if arrow == 'Serifs1':
            newpoints.append([width-center2, depth / 2, 0]) #16
            newpoints.append([width-center2, dsize / 2, 0]) #17
            newpoints.append([width + center1, dsize / 2, 0]) #18
            newpoints.append([width + center1, depth / 2 + b, 0]) #19
        else:
            newpoints.append([width + center1-w * b, depth / 2, 0]) #19
        newpoints.append([width + center1 + x, depth / 2 + b + y, 0]) #20
        newpoints.append([width + center1 + w * b + x, depth / 2 + y, 0]) #21
        newpoints.append([width + center1 + w * b, depth / 2, 0]) #22
        newpoints.append([width + center1 + w * length, depth / 2, 0]) #23
        newpoints.append([width + center1 + w * length, -depth / 2, 0]) #24
        if arrow == 'Serifs1':
            newpoints.append([width + center1, -depth / 2, 0]) #25
            newpoints.append([width + center1, -dsize / 2, 0]) #26
            newpoints.append([width-center2, -dsize / 2, 0]) #29
            newpoints.append([width-center2, -depth / 2-b, 0]) #30
        else:
            newpoints.append([width-center2 + w * b, -depth / 2, 0]) #30
        newpoints.append([width-center2-x, -depth / 2-b-y, 0]) #31
        newpoints.append([width-center2-w * b-x, -depth / 2-y, 0]) #32
        newpoints.append([width-center2-w * b, -depth / 2, 0]) #33
        newpoints.append([0, -depth / 2, 0]) #10
        if arrow == 'Serifs1':
            newpoints.append([-width + center2, -depth / 2, 0]) #25
            newpoints.append([-width + center2, -dsize / 2, 0]) #26
            newpoints.append([-width-center1, -dsize / 2, 0]) #29
            newpoints.append([-width-center1, -depth / 2-b, 0]) #30
        else:
            newpoints.append([-width-center1 + w * b, -depth / 2, 0]) #30
        newpoints.append([-width-center1-x, -depth / 2-b-y, 0]) #31
        newpoints.append([-width-center1-w * b-x, -depth / 2-y, 0]) #32
        newpoints.append([-width-center1-w * b, -depth / 2, 0]) #33
        newpoints.append([-width + center2-w * length, -depth / 2, 0]) #24
        newpoints.append([-width + center2-w * length, depth / 2, 0]) #23
        if arrow == 'Serifs1':
            newpoints.append([-width-center1, depth / 2, 0]) #16
            newpoints.append([-width-center1, dsize / 2, 0]) #17
            newpoints.append([-width + center2, dsize / 2, 0]) #18
            newpoints.append([-width + center2, depth / 2 + b, 0]) #19
        else:
            newpoints.append([-width + center2-w * b, depth / 2, 0]) #19
        newpoints.append([-width + center2 + x, depth / 2 + b + y, 0]) #20
        newpoints.append([-width + center2 + w * b + x, depth / 2 + y, 0]) #21
        newpoints.append([-width + center2 + w * b, depth / 2, 0]) #22

    if arrow == 'Without':
        newpoints.append([0, depth / 2, 0]) #1
        newpoints.append([width, depth / 2, 0]) #2
        newpoints.append([width, -depth / 2, 0]) #9
        newpoints.append([0, -depth / 2, 0]) #10
        newpoints.append([-width, -depth / 2, 0]) #11
        newpoints.append([-width, depth / 2, 0]) #18

    return newpoints

##------------------------------------------------------------
# Dimension: Angular1
def Angular1(width = 2, length = 2, depth = 0.1, angle = 45, resolution = 10, center = False, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        arrow = 'Without'

    w = 1
    if width < 0:
        w = -1

    if resolution == 0:
       resolution = 1

    if arrow == 'Without':
       arrowdepth = 0.0
       arrowlength = 0.0

    length = abs(length)
    angle = radians(angle)

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    g = hypot(width + w * length, center2)
    u_depth = asin((center2) / g)

    g = hypot(width, center2)
    u_depth_min = asin((center2 + center2/4) / g)

    g = hypot(width, arrowlength + w * center2)
    u_arrow = asin((arrowlength + w * center2) / g)

    if width < 0:
        u_depth = -u_depth
        u_depth_min = -u_depth_min

    a = 1
    if angle < 0 :
       a = -1
       u_depth = -u_depth
       u_depth_min = -u_depth_min
       u_arrow = -u_arrow

    x = (a * center1) / tan(angle / 2)
    newpoints.append([-x, -a * center1, 0]) #1
    newpoints.append([width + w * length, -a * center1, 0]) #2
    newpoints.append([width + w * length, a * center2, 0]) #3

    if arrow == 'Without':
        newpoints.append([width + w * depth / 2, a * center2, 0]) #4
    else:
        newpoints.append([width + w * depth / 100, a * center2, 0]) #4

    g = width + w * arrowdepth + w * depth / 2
    x = cos(u_arrow + u_depth) * g
    y = sin(u_arrow + u_depth) * g
    newpoints.append([x, y, 0]) #5

    if arrow == 'Arrow1':
        g = width + w * depth / 2
        x = cos(u_arrow + u_depth) * g
        y = sin(u_arrow + u_depth) * g
        newpoints.append([x, y, 0]) #6
    if arrow == 'Arrow2':
        g = width + w * depth / 2
        x = cos(u_arrow * 3 / 4 + u_depth) * g
        y = sin(u_arrow * 3 / 4 + u_depth) * g
        newpoints.append([x, y, 0]) #6

    i = 1
    while i < resolution :
        u = i * (angle - u_arrow * 2 - u_depth * 2) / resolution
        g = width + w * depth / 2
        x = cos(u + u_arrow + u_depth) * g
        y = sin(u + u_arrow + u_depth) * g
        newpoints.append([x, y, 0]) #n
        i  += 1

    if arrow == 'Arrow1':
        g = width + w * depth / 2
        x = cos(angle - u_arrow - u_depth) * g
        y = sin(angle - u_arrow - u_depth) * g
        newpoints.append([x, y, 0]) #7
    if arrow == 'Arrow2':
        g = width + w * depth / 2
        x = cos(angle - u_arrow * 3 / 4 - u_depth) * g
        y = sin(angle - u_arrow * 3 / 4 - u_depth) * g
        newpoints.append([x, y, 0]) #7

    u = angle - u_arrow - u_depth
    g = width + w * arrowdepth + w * depth / 2
    x = cos(u) * g
    y = sin(u) * g
    newpoints.append([x, y, 0]) #8

    if arrow == 'Without':
        g = width + w * depth / 2
        x = cos(angle-u_depth_min) * g
        y = sin(angle-u_depth_min) * g
        newpoints.append([x, y, 0]) #9
    else:
        g = width + w * depth / 100
        x = cos(angle-u_depth_min) * g
        y = sin(angle-u_depth_min) * g
        newpoints.append([x, y, 0]) #9

    if arrow == 'Without':
        g = width-w * depth / 2
        x = cos(angle-u_depth_min) * g
        y = sin(angle-u_depth_min) * g
        newpoints.append([x, y, 0]) #10
    else:
        g = width-w * depth / 100
        x = cos(angle-u_depth_min) * g
        y = sin(angle-u_depth_min) * g
        newpoints.append([x, y, 0]) #10

    g = width-w * arrowdepth-w * depth / 2
    x = cos(u) * g
    y = sin(u) * g
    newpoints.append([x, y, 0]) #11

    if arrow == 'Arrow1':
        u = angle - u_arrow - u_depth
        g = width-w * depth / 2
        x = cos(u) * g
        y = sin(u) * g
        newpoints.append([x, y, 0]) #12
    if arrow == 'Arrow2':
        u = angle - u_arrow * 3 / 4 - u_depth
        g = width-w * depth / 2
        x = cos(u) * g
        y = sin(u) * g
        newpoints.append([x, y, 0]) #12

    i = resolution - 1
    while i >=  1 :
        u = i * (angle - u_arrow * 2 - u_depth * 2) / resolution
        g = width-w * depth / 2
        x = cos(u + u_arrow + u_depth) * g
        y = sin(u + u_arrow + u_depth) * g
        newpoints.append([x, y, 0]) #n
        i -=  1

    if arrow == 'Arrow1':
        g = width-w * depth / 2
        x = cos(u_arrow + u_depth) * g
        y = sin(u_arrow + u_depth) * g
        newpoints.append([x, y, 0]) #13
    if arrow == 'Arrow2':
        g = width-w * depth / 2
        x = cos(u_arrow * 3 / 4 + u_depth) * g
        y = sin(u_arrow * 3 / 4 + u_depth) * g
        newpoints.append([x, y, 0]) #13

    g = width-w * arrowdepth-w * depth / 2
    x = cos(u_arrow + u_depth) * g
    y = sin(u_arrow + u_depth) * g
    newpoints.append([x, y, 0]) #14

    if arrow == 'Without':
        newpoints.append([width-w * depth / 2, a * center2, 0]) #15
    else:
        newpoints.append([width-w * depth / 100, a * center2, 0]) #15

    x = (a * center2) / tan(angle / 2)
    newpoints.append([x, a * center2, 0]) #16

    g = width + w * length
    x = cos(angle-u_depth) * g
    y = sin(angle-u_depth) * g
    newpoints.append([x, y, 0]) #17

    if center:
        g = width + w * length
        x = cos(angle + u_depth) * g
        y = sin(angle + u_depth) * g
        newpoints.append([x, y, 0]) #18
    else:
        g = width + w * length
        x = cos(angle) * g
        y = sin(angle) * g
        newpoints.append([x, y, 0]) #18

    return newpoints

##------------------------------------------------------------
# Dimension: Angular2
def Angular2(width = 2, depth = 0.1, angle = 45, resolution = 10, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        arrow = 'Without'

    w = 1
    if width < 0:
        w = -1

    if resolution == 0:
       resolution = 1

    if arrow == 'Without':
       arrowdepth = 0.0
       arrowlength = 0.0

    angle = radians(angle)

    newpoints.append([width, 0, 0]) #1

    g = hypot(width + w * depth / 2, arrowlength)
    u_arrow = asin((arrowlength) / g)
    if angle < 0 :
       u_arrow = -u_arrow

    g = width + w * arrowdepth + w * depth / 2
    x = cos(u_arrow) * g
    y = sin(u_arrow) * g
    newpoints.append([x, y, 0]) #2

    if arrow == 'Arrow1':
        g = width + w * depth / 2
        x = cos(u_arrow) * g
        y = sin(u_arrow) * g
        newpoints.append([x, y, 0]) #3

    if arrow == 'Arrow2':
        g = width + w * depth / 2
        x = cos(u_arrow * 3 / 4) * g
        y = sin(u_arrow * 3 / 4) * g
        newpoints.append([x, y, 0]) #3

    i = 1
    while i < resolution :
        u = i * (angle - u_arrow * 2) / resolution
        g = width + w * depth / 2
        x = cos(u + u_arrow) * g
        y = sin(u + u_arrow) * g
        newpoints.append([x, y, 0]) #n
        i  += 1

    if arrow == 'Arrow1':
        u = angle - u_arrow
        g = width + w * depth / 2
        x = cos(u) * g
        y = sin(u) * g
        newpoints.append([x, y, 0]) #4
    if arrow == 'Arrow2':
        u = angle - u_arrow * 3 / 4
        g = width + w * depth / 2
        x = cos(u) * g
        y = sin(u) * g
        newpoints.append([x, y, 0]) #4

    u = angle - u_arrow
    g = width + w * arrowdepth + w * depth / 2
    x = cos(u) * g
    y = sin(u) * g
    newpoints.append([x, y, 0]) #5

    g = width
    x = cos(angle) * g
    y = sin(angle) * g
    newpoints.append([x, y, 0]) #6

    g = width-w * arrowdepth-w * depth / 2
    x = cos(u) * g
    y = sin(u) * g
    newpoints.append([x, y, 0]) #7

    if arrow == 'Arrow1':
        u = angle - u_arrow
        g = width-w * depth / 2
        x = cos(u) * g
        y = sin(u) * g
        newpoints.append([x, y, 0]) #8
    if arrow == 'Arrow2':
        u = angle - u_arrow * 3 / 4
        g = width-w * depth / 2
        x = cos(u) * g
        y = sin(u) * g
        newpoints.append([x, y, 0]) #8

    i = resolution - 1
    while i > 0 :
        u = i * (angle - u_arrow * 2) / resolution
        g = width-w * depth / 2
        x = cos(u + u_arrow) * g
        y = sin(u + u_arrow) * g
        newpoints.append([x, y, 0]) #n
        i -=  1

    if arrow == 'Arrow1':
        g = width-w * depth / 2
        x = cos(u_arrow) * g
        y = sin(u_arrow) * g
        newpoints.append([x, y, 0]) #9
    if arrow == 'Arrow2':
        g = width-w * depth / 2
        x = cos(u_arrow * 3 / 4) * g
        y = sin(u_arrow * 3 / 4) * g
        newpoints.append([x, y, 0]) #9

    g = width-w * arrowdepth-w * depth / 2
    x = cos(u_arrow) * g
    y = sin(u_arrow) * g
    newpoints.append([x, y, 0]) #10

    return newpoints

##------------------------------------------------------------
# Dimension: Angular3
def Angular3(width = 2, length = 2, dsize = 1, depth = 0.1, angle = 45, resolution = 10, center = False, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        arrow = 'Without'

    w = 1
    if width < 0:
        w = -1

    if resolution == 0:
       resolution = 1

    if arrow == 'Without':
       arrowdepth = 0.0
       arrowlength = 0.0

    resolution_2 = floor(resolution / 2)

    length = abs(length)
    angle = radians(angle)

    if center:
       center1 = w * depth / 2
       center2 = w * depth / 2
    else:
       center1 = 0
       center2 = w * depth

    g = hypot(width + w * length, center2)
    u_depth = asin((center2) / g)

    g = hypot(width + depth / 2, center2)
    u_depth_13 = asin((center2 + center2/4) / g)

    g = hypot(width-depth / 2, center2)
    u_depth_14 = asin((center2 + center2/4) / g)

    g = hypot(width, center2)
    u_depth_min = asin((center2) / g)

    g = hypot(width, arrowlength + w * center2)
    u_arrow = asin((arrowlength + w * center2) / g)

    g = hypot(width, arrowlength + w * center2 + dsize)
    u_dsize = asin((arrowlength + w * center2 + dsize) / g)

    if width < 0:
        u_depth = -u_depth
        u_depth_min = -u_depth_min
        u_depth_13 = -u_depth_13
        u_depth_14 = -u_depth_14

    a = 1
    if angle < 0 :
       a = -1
       u_depth = -u_depth
       u_depth_min = -u_depth_min
       u_arrow = -u_arrow
       u_depth_13 = -u_depth_13
       u_depth_14 = -u_depth_14

    x = (a * center1) / tan(angle / 2)
    newpoints.append([-x, -a * center1, 0]) #1

    if arrow == 'Without':
        newpoints.append([width-w * depth / 2, -a * center1, 0]) #2
    else:
        newpoints.append([width-w * depth / 100, -a * center1, 0]) #2

    g = width-w * arrowdepth-w * depth / 2
    x = cos(-u_arrow-u_depth) * g
    y = sin(-u_arrow-u_depth) * g
    newpoints.append([x, y, 0]) #3

    if arrow == 'Arrow1':
        g = width-w * depth / 2
        x = cos(-u_arrow-u_depth) * g
        y = sin(-u_arrow-u_depth) * g
        newpoints.append([x, y, 0]) #4
    if arrow == 'Arrow2':
        g = width-w * depth / 2
        x = cos(-u_arrow * 3 / 4-u_depth) * g
        y = sin(-u_arrow * 3 / 4-u_depth) * g
        newpoints.append([x, y, 0]) #4

    i = 1
    while i < resolution_2 :
        u = i * (-u_dsize) / resolution_2
        g = width-w * depth / 2
        x = cos(u-u_arrow) * g
        y = sin(u-u_arrow) * g
        newpoints.append([x, y, 0]) #n
        i  += 1

    g = width-w * depth / 2
    x = cos(-u_arrow-u_depth-u_dsize) * g
    y = sin(-u_arrow-u_depth-u_dsize) * g
    newpoints.append([x, y, 0]) #5

    g = width + w * depth / 2
    x = cos(-u_arrow-u_depth-u_dsize) * g
    y = sin(-u_arrow-u_depth-u_dsize) * g
    newpoints.append([x, y, 0]) #6

    i = resolution_2
    while i >=  1 :
        u = i * (-u_dsize) / resolution_2
        g = width + w * depth / 2
        x = cos(u-u_arrow) * g
        y = sin(u-u_arrow) * g
        newpoints.append([x, y, 0]) #n
        i -=  1

    if arrow == 'Arrow1':
       g = width + w * depth / 2
       x = cos(-u_arrow-u_depth) * g
       y = sin(-u_arrow-u_depth) * g
       newpoints.append([x, y, 0]) #7
    if arrow == 'Arrow2':
       g = width + w * depth / 2
       x = cos(-u_arrow * 3 / 4-u_depth) * g
       y = sin(-u_arrow * 3 / 4-u_depth) * g
       newpoints.append([x, y, 0]) #7

    g = width + w * arrowdepth + w * depth / 2
    x = cos(-u_arrow-u_depth) * g
    y = sin(-u_arrow-u_depth) * g
    newpoints.append([x, y, 0]) #8

    if arrow == 'Without':
        newpoints.append([width + w * depth / 2, -a * center1, 0]) #9
    else:
        newpoints.append([width + w * depth / 100, -a * center1, 0]) #9

    newpoints.append([width + w * length, -a * center1, 0]) #10

    newpoints.append([width + w * length, a * center2, 0]) #11

    g = width + w * depth / 2
    x = cos(u_depth_min) * g
    y = sin(u_depth_min) * g
    newpoints.append([x, y, 0]) #12

    i = 1
    while i < resolution :
        u = i * (angle - u_depth * 2) / resolution
        g = width + w * depth / 2
        x = cos(u + u_depth) * g
        y = sin(u + u_depth) * g
        newpoints.append([x, y, 0]) #n
        i  += 1

    if width > 0 :
        g = width + w * depth / 2
        x = cos(angle - u_depth_13) * g
        y = sin(angle - u_depth_13) * g
        newpoints.append([x, y, 0]) #13

        g = width-w * depth / 2
        x = cos(angle - u_depth_14) * g
        y = sin(angle - u_depth_14) * g
        newpoints.append([x, y, 0]) #14
    else:
        g = width + w * depth / 2
        x = cos(angle - u_depth_14) * g
        y = sin(angle - u_depth_14) * g
        newpoints.append([x, y, 0]) #13

        g = width-w * depth / 2
        x = cos(angle - u_depth_13) * g
        y = sin(angle - u_depth_13) * g
        newpoints.append([x, y, 0]) #14

    i = resolution - 1
    while i >=  1 :
        u = i * (angle - u_depth * 2) / resolution
        g = width-w * depth / 2
        x = cos(u + u_depth) * g
        y = sin(u + u_depth) * g
        newpoints.append([x, y, 0]) #n
        i -=  1

    g = width-w * depth / 2
    x = cos(u_depth_min) * g
    y = sin(u_depth_min) * g
    newpoints.append([x, y, 0]) #15

    x = (a * center2) / tan(angle / 2)
    newpoints.append([x, a * center2, 0]) #16

    g = width + w * length
    x = cos(angle-u_depth) * g
    y = sin(angle-u_depth) * g
    newpoints.append([x, y, 0]) #17

    if center:
        g = width + w * length
        x = cos(angle + u_depth) * g
        y = sin(angle + u_depth) * g
        newpoints.append([x, y, 0]) #18

        if arrow == 'Without':
            g = width + w * depth / 2
            x = cos(angle + u_depth) * g
            y = sin(angle + u_depth) * g
            newpoints.append([x, y, 0]) #19
        else:
            g = width + w * depth / 100
            x = cos(angle + u_depth) * g
            y = sin(angle + u_depth) * g
            newpoints.append([x, y, 0]) #19
    else:
        g = width + w * length
        x = cos(angle) * g
        y = sin(angle) * g
        newpoints.append([x, y, 0]) #18

        if arrow == 'Without':
            g = width + w * depth / 2
            x = cos(angle) * g
            y = sin(angle) * g
            newpoints.append([x, y, 0]) #19
        else:
            g = width + w * depth / 100
            x = cos(angle) * g
            y = sin(angle) * g
            newpoints.append([x, y, 0]) #19

    g = width + w * arrowdepth + w * depth / 2
    x = cos(angle + u_arrow + u_depth) * g
    y = sin(angle + u_arrow + u_depth) * g
    newpoints.append([x, y, 0]) #20

    if arrow == 'Arrow1':
        g = width + w * depth / 2
        x = cos(angle + u_arrow + u_depth) * g
        y = sin(angle + u_arrow + u_depth) * g
        newpoints.append([x, y, 0]) #21
    if arrow == 'Arrow2':
        g = width + w * depth / 2
        x = cos(angle + u_arrow * 3 / 4 + u_depth) * g
        y = sin(angle + u_arrow * 3 / 4 + u_depth) * g
        newpoints.append([x, y, 0]) #21

    i = 1
    while i < resolution_2 :
        u = i * (u_dsize) / resolution_2
        g = width + w * depth / 2
        x = cos(u + angle + u_arrow) * g
        y = sin(u + angle + u_arrow) * g
        newpoints.append([x, y, 0]) #n
        i  += 1

    g = width + w * depth / 2
    x = cos(angle + u_arrow + u_depth + u_dsize) * g
    y = sin(angle + u_arrow + u_depth + u_dsize) * g
    newpoints.append([x, y, 0]) #22

    g = width-w * depth / 2
    x = cos(angle + u_arrow + u_depth + u_dsize) * g
    y = sin(angle + u_arrow + u_depth + u_dsize) * g
    newpoints.append([x, y, 0]) #23

    i = resolution_2
    while i >=  1 :
        u = i * (u_dsize) / resolution_2
        g = width-w * depth / 2
        x = cos(u + angle + u_arrow) * g
        y = sin(u + angle + u_arrow) * g
        newpoints.append([x, y, 0]) #n
        i -=  1

    if arrow == 'Arrow1':
        g = width-w * depth / 2
        x = cos(angle + u_arrow + u_depth) * g
        y = sin(angle + u_arrow + u_depth) * g
        newpoints.append([x, y, 0]) #24
    if arrow == 'Arrow2':
        g = width-w * depth / 2
        x = cos(angle + u_arrow * 3 / 4 + u_depth) * g
        y = sin(angle + u_arrow * 3 / 4 + u_depth) * g
        newpoints.append([x, y, 0]) #24

    g = width-w * arrowdepth-w * depth / 2
    x = cos(angle + u_arrow + u_depth) * g
    y = sin(angle + u_arrow + u_depth) * g
    newpoints.append([x, y, 0]) #25

    if center:
        if arrow == 'Without':
            g = width-w * depth / 2
            x = cos(angle + u_depth) * g
            y = sin(angle + u_depth) * g
            newpoints.append([x, y, 0]) #26
        else:
            g = width-w * depth / 100
            x = cos(angle + u_depth) * g
            y = sin(angle + u_depth) * g
            newpoints.append([x, y, 0]) #26
    else:
        if arrow == 'Without':
            g = width-w * depth / 2
            x = cos(angle) * g
            y = sin(angle) * g
            newpoints.append([x, y, 0]) #26
        else:
            g = width-w * depth / 100
            x = cos(angle) * g
            y = sin(angle) * g
            newpoints.append([x, y, 0]) #26

    return newpoints

##------------------------------------------------------------
# Dimension: Note
def Note(width = 2, length = 2, depth = 0.1, angle = 45, arrow = 'Arrow1', arrowdepth = 0.25, arrowlength = 0.25):

    newpoints = []

    if arrow == 'Serifs1' or arrow == 'Serifs2':
        arrow = 'Without'

    w = 1
    if width < 0:
        w = -1
    angle = radians(angle)
    length = abs(length)

    if cos(angle) > 0:
        newpoints.append([0, 0, 0]) #1

        if arrow == 'Arrow1':
            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #2

            g = hypot(arrowlength, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #3

        if arrow == 'Arrow2':
            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #2

            g = hypot(arrowlength * 3 / 4, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #3

        if arrow == 'Without':
            g = w * depth / 2
            x = cos(angle + radians(90)) * g
            y = sin(angle + radians(90)) * g
            newpoints.append([x, y, 0]) #2

        g = hypot(width, depth / 2)
        u = asin((depth / 2) / g)
        x = cos(angle + u) * g
        y = sin(angle) * width
        newpoints.append([w * x, y + w * depth / 2, 0]) #4

        newpoints.append([w * x + w * length, y + w * depth / 2, 0]) #5
        newpoints.append([w * x + w * length, y-w * depth / 2, 0]) #6

        g = hypot(width, depth / 2)
        u = asin((depth / 2) / g)
        y = sin(angle) * width
        x = cos(angle-u) * g
        newpoints.append([w * x, y-w * depth / 2, 0]) #7

        if arrow == 'Arrow1':
            g = hypot(arrowlength, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #8

            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #9

        if arrow == 'Arrow2':
            g = hypot(arrowlength * 3 / 4, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #8

            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #9

        if arrow == 'Without':
            g = -w * depth / 2
            x = cos(angle + radians(90)) * g
            y = sin(angle + radians(90)) * g
            newpoints.append([x, y, 0]) #6

    else:
        newpoints.append([0, 0, 0]) #1

        if arrow == 'Arrow1':
            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #2

            g = hypot(arrowlength, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #3

        if arrow == 'Arrow2':
            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #2

            g = hypot(arrowlength * 3 / 4, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle-u) * g
            y = sin(angle-u) * g
            newpoints.append([w * x, y, 0]) #3

        if arrow == 'Without':
            g = -w * depth / 2
            x = cos(angle + radians(90)) * g
            y = sin(angle + radians(90)) * g
            newpoints.append([x, y, 0]) #2

        g = hypot(width, depth / 2)
        u = asin((depth / 2) / g)
        x = cos(angle-u) * g
        y = sin(angle) * width
        newpoints.append([w * x, y + w * depth / 2, 0]) #4

        newpoints.append([w * x-w * length, y + w * depth / 2, 0]) #5
        newpoints.append([w * x-w * length, y-w * depth / 2, 0]) #6

        g = hypot(width, depth / 2)
        u = asin((depth / 2) / g)
        y = sin(angle) * width
        x = cos(angle + u) * g
        newpoints.append([w * x, y-w * depth / 2, 0]) #7

        if arrow == 'Arrow1':
            g = hypot(arrowlength, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #8

            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #9

        if arrow == 'Arrow2':
            g = hypot(arrowlength * 3 / 4, depth / 2)
            u = asin((depth / 2) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #8

            g = hypot(arrowlength, depth / 2 + arrowdepth)
            u = asin((depth / 2 + arrowdepth) / g)
            x = cos(angle + u) * g
            y = sin(angle + u) * g
            newpoints.append([w * x, y, 0]) #9

        if arrow == 'Without':
            g = w * depth / 2
            x = cos(angle + radians(90)) * g
            y = sin(angle + radians(90)) * g
            newpoints.append([x, y, 0]) #6

    return newpoints

##------------------------------------------------------------
# make and set Material
def makeMaterial(name, diffuse, specular, alpha):

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = 1.0
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 1.0
    mat.alpha = alpha
    mat.ambient = 1
    mat.specular_hardness = 1
    mat.use_shadeless = True

    return mat

def setMaterial(ob, mat):

    me = ob.data
    me.materials.append(mat)

def ablength(x1 = 0.0, y1 = 0.0, z1 = 0.0, x2 = 0.0, y2 = 0.0, z2 = 0.0):
  return sqrt( (x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2 )

##------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref
def align_matrix(context, location):

    loc = Matrix.Translation(location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.to_3x3().inverted().to_4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot

    return align_matrix

##------------------------------------------------------------
#### Curve creation functions
# sets bezierhandles to auto
def setBezierHandles(obj, mode = 'VECTOR'):

    scene = bpy.context.scene
    if obj.type !=  'CURVE':
        return
    scene.objects.active = obj
    bpy.ops.object.mode_set(mode = 'EDIT', toggle = True)
    bpy.ops.curve.select_all(action = 'SELECT')
    bpy.ops.curve.handle_type_set(type = mode)
    bpy.ops.object.mode_set(mode = 'OBJECT', toggle = True)
    bpy.context.scene.update()

##------------------------------------------------------------
#### Add units
def addUnits(stext, units):
    scale = bpy.context.scene.unit_settings.scale_length
    unit_system = bpy.context.scene.unit_settings.system
    separate_units = bpy.context.scene.unit_settings.use_separate
    if unit_system == 'METRIC':
        if units == 'None': scale_steps = 1
        if units == '\u00b5m': scale_steps = 1000000
        if units == 'mm': scale_steps = 1000
        if units == 'cm': scale_steps = 100
        if units == 'm': scale_steps = 1
        if units == 'km': scale_steps = 1/1000
        if units == 'thou': scale_steps = 36000 * 1.0936133
        if units == '"': scale_steps = 36 * 1.0936133
        if units == '\'': scale_steps = 3 * 1.0936133
        if units == 'yd': scale_steps = 1 * 1.0936133
        if units == 'mi': scale_steps = 1/1760 * 1.0936133
        dval = stext * scale_steps * scale
    elif unit_system == 'IMPERIAL':
        if units == 'None': scale_steps = 3 * 1.0936133
        if units == '\u00b5m': scale_steps = 1000000
        if units == 'mm': scale_steps = 1000
        if units == 'cm': scale_steps = 100
        if units == 'm': scale_steps = 1
        if units == 'km': scale_steps = 1/1000
        if units == 'thou': scale_steps = 36000 * 1.0936133
        if units == '"': scale_steps = 36 * 1.0936133
        if units == '\'': scale_steps = 3 * 1.0936133
        if units == 'yd': scale_steps = 1 * 1.0936133
        if units == 'mi': scale_steps = 1/1760 * 1.0936133
        dval = stext * scale_steps * scale
    else:
        dval = stext
    return dval
##------------------------------------------------------------
# create new CurveObject from vertarray and splineType
def createCurve(vertArray, self, align_matrix):
    # options to vars
    name = self.Dimension_Type         # Type as name

    # create curve
    scene = bpy.context.scene
    newCurve = bpy.data.curves.new(name, type = 'CURVE') # curvedatablock
    newSpline = newCurve.splines.new('BEZIER') # spline

    newSpline.bezier_points.add(int(len(vertArray) * 0.333333333))
    newSpline.bezier_points.foreach_set('co', vertArray)

    # set curveOptions
    newCurve.dimensions = '2D'
    newSpline.use_cyclic_u = True
    newSpline.use_endpoint_u = True

    # create object with newCurve
    DimensionCurve = bpy.data.objects.new(name, newCurve) # object
    scene.objects.link(DimensionCurve) # place in active scene
    DimensionCurve.Dimension = True
    DimensionCurve.matrix_world = align_matrix # apply matrix
    self.Dimension_Name = DimensionCurve.name

    # creat DimensionText and rotation
    w = 1
    if self.Dimension_width < 0 :
        w = -1
    l = 1
    if self.Dimension_length < 0 :
        l = -1

    x = self.Dimension_width / 2
    y = self.Dimension_length + l * self.Dimension_dsize / 2 + self.Dimension_depth / 2 + self.Dimension_textdepth

    gettextround = int(self.Dimension_textround)
    stext = addUnits(self.Dimension_width, self.Dimension_units)
    stext = abs(round(stext, gettextround))
    if gettextround == 0:
        stext = abs(int(stext))

    align = 'CENTER'
    offset_y = 0

    if self.Dimension_Type == 'Linear-2':
        y = self.Dimension_depth / 2 + self.Dimension_textdepth

    if self.Dimension_Type == 'Radius':
        x = self.Dimension_width + w * self.Dimension_dsize / 2 + w * abs(self.Dimension_length) / 2
        y = self.Dimension_depth / 2 + self.Dimension_textdepth

    if self.Dimension_Type == 'Diameter':
        x = 0
        y = self.Dimension_depth / 2 + self.Dimension_textdepth

    g = hypot(x, y)
    c = self.Dimension_startlocation
    u = asin(y / g)
    if self.Dimension_width < 0 :
        u = radians(180) - u
    xx = cos(u) * g
    yy = sin(u) * g

    stext = str(stext)
    if self.Dimension_units != 'None' and self.Dimension_add_units_name:
        stext += self.Dimension_units

    if self.Dimension_Type == 'Angular1' or self.Dimension_Type == 'Angular2' or self.Dimension_Type == 'Angular3':
        xx = cos(radians(self.Dimension_angle / 2)) * (self.Dimension_width + w * self.Dimension_depth / 2 + w * self.Dimension_textdepth)
        yy = sin(radians(self.Dimension_angle / 2)) * (self.Dimension_width + w * self.Dimension_depth / 2 + w * self.Dimension_textdepth)
        system_rotation = bpy.context.scene.unit_settings.system_rotation
        if system_rotation == 'DEGREES':
            stext = abs(round(self.Dimension_angle, gettextround))
            if gettextround == 0:
                stext = abs(int(stext))
            stext = str(stext) + '°'
        else:
            stext = abs(round(self.Dimension_angle * pi / 180, gettextround))
            if gettextround == 0:
                stext = abs(int(stext))
            stext = str(stext)
        align = 'LEFT'
        if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
            align = 'RIGHT'
        if self.Dimension_width < 0 :
            offset_y = 0
            align = 'RIGHT'
            if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
                align = 'LEFT'

    if self.Dimension_Type == 'Note':
        if cos(radians(self.Dimension_angle)) > 0:
            xx = cos(radians(self.Dimension_angle)) * (self.Dimension_width) + l * w * self.Dimension_depth / 2 + l * w * self.Dimension_textdepth
            yy = sin(radians(self.Dimension_angle)) * (self.Dimension_width) + w * self.Dimension_depth / 2 + w * self.Dimension_textdepth
            stext = self.Dimension_note
            align = 'LEFT'
            if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
                align = 'RIGHT'
            if self.Dimension_width < 0 :
                align = 'RIGHT'
                xx = cos(radians(self.Dimension_angle)) * (self.Dimension_width) + l * w * self.Dimension_depth / 2 + l * w * self.Dimension_textdepth
                yy = sin(radians(self.Dimension_angle)) * (self.Dimension_width) - w * self.Dimension_depth / 2 - w * self.Dimension_textdepth
                if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
                   align = 'LEFT'
        else:
            xx = cos(radians(self.Dimension_angle)) * (self.Dimension_width) - l * w * self.Dimension_depth / 2 - l * w * self.Dimension_textdepth
            yy = sin(radians(self.Dimension_angle)) * (self.Dimension_width) + w * self.Dimension_depth / 2 + w * self.Dimension_textdepth
            stext = self.Dimension_note
            align = 'RIGHT'
            if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
                align = 'LEFT'
            if self.Dimension_width < 0 :
                align = 'LEFT'
                xx = cos(radians(self.Dimension_angle)) * (self.Dimension_width) - l * w * self.Dimension_depth / 2 - l * w * self.Dimension_textdepth
                yy = sin(radians(self.Dimension_angle)) * (self.Dimension_width) - w * self.Dimension_depth / 2 - w * self.Dimension_textdepth
                if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
                    align = 'RIGHT'

    if self.Dimension_liberty == '2D':
        tv = Vector((xx, yy, 0))

        DimensionText = addText(stext, tv, self.Dimension_textsize, align, offset_y, self.Dimension_font)

        if self.Dimension_XYZType == 'TOP' or self.Dimension_XYZType == 'BOTTOM':
            DimensionCurve.rotation_euler[0] = radians(0)
            DimensionCurve.rotation_euler[1] = radians(0)
            if self.Dimension_XYType == 'X':
                DimensionCurve.rotation_euler[2] = radians(self.Dimension_rotation)
                DimensionCurve.location[1] += self.Dimension_offset
            if self.Dimension_XYType == 'Y':
                DimensionCurve.rotation_euler[2] = radians(90+self.Dimension_rotation)
                DimensionCurve.location[0] += self.Dimension_offset

        if self.Dimension_XYZType == 'FRONT' or self.Dimension_XYZType == 'BACK':
            DimensionCurve.rotation_euler[0] = radians(90)
            if self.Dimension_XZType == 'X':
                DimensionCurve.rotation_euler[1] = -radians(self.Dimension_rotation)
                DimensionCurve.location[1] += self.Dimension_offset
            if self.Dimension_XZType == 'Z':
                DimensionCurve.rotation_euler[1] = -radians(90+self.Dimension_rotation)
                DimensionCurve.location[0] += self.Dimension_offset
            DimensionCurve.rotation_euler[2] = radians(0)

        if self.Dimension_XYZType == 'RIGHT' or self.Dimension_XYZType == 'LEFT':
            DimensionCurve.rotation_euler[0] = radians(90)
            if self.Dimension_YZType == 'Y':
                DimensionCurve.rotation_euler[1] = -radians(self.Dimension_rotation)
                DimensionCurve.location[0] += self.Dimension_offset
            if self.Dimension_YZType == 'Z':
                DimensionCurve.rotation_euler[1] = -radians(90+self.Dimension_rotation)
                DimensionCurve.location[1] += self.Dimension_offset
            DimensionCurve.rotation_euler[2] = radians(90)

        if self.Dimension_XYZType == 'TOP' or self.Dimension_XYZType == 'FRONT' or self.Dimension_XYZType == 'RIGHT':
            DimensionText.rotation_euler[1] = radians(0)
        if self.Dimension_XYZType == 'BOTTOM' or self.Dimension_XYZType == 'BACK' or self.Dimension_XYZType == 'LEFT':
            DimensionText.rotation_euler[1] = radians(180)

        if self.Dimension_width_or_location == 'location':
            if self.Dimension_Type == 'Angular1' or self.Dimension_Type == 'Angular2' or self.Dimension_Type == 'Angular3':
                vx = self.Dimension_endlocation.x - self.Dimension_startlocation.x
                vy = self.Dimension_endlocation.y - self.Dimension_startlocation.y
                vz = self.Dimension_endlocation.z - self.Dimension_startlocation.z
                if self.Dimension_XYZType == 'TOP' or self.Dimension_XYZType == 'BOTTOM':
                    g = hypot(vx, vy)
                    if g !=  0 :
                       u2 = acos(vx / g)
                       u1 = asin(vy / g)
                       if u1 < 0 :
                           u2 = u1
                    else:
                       u2 = 0
                    DimensionCurve.rotation_euler[2] = u2

                if self.Dimension_XYZType == 'FRONT' or self.Dimension_XYZType == 'BACK':
                    g = hypot(vx, vz)
                    if g !=  0 :
                       u2 = acos(vx / g)
                       u1 = asin(vz / g)
                       if u1 < 0 :
                           u2 = u1
                    else:
                       u2 = 0
                    DimensionCurve.rotation_euler[1] = -u2

                if self.Dimension_XYZType == 'RIGHT' or self.Dimension_XYZType == 'LEFT':
                    g = hypot(vy, vz)
                    if g !=  0 :
                       u2 = acos(vy / g)
                       u1 = asin(vz / g)
                       if u1 < 0 :
                           u2 = u1
                    else:
                       u2 = 0
                    DimensionCurve.rotation_euler[1] = -u2

    if self.Dimension_liberty == '3D':
        tv = Vector((xx, yy, 0))
        DimensionText = addText(stext, tv, self.Dimension_textsize, align, offset_y, self.Dimension_font)
        v = self.Dimension_endlocation - self.Dimension_startlocation
        if v.length !=  0 :
           u1 = -asin(v[2] / v.length)
        else:
           u1 = 0
        g = hypot(v[0], v[1])
        if g !=  0 :
           u2 = asin(v[1] / g)
           if self.Dimension_endlocation.x < self.Dimension_startlocation.x :
              u2 = radians(180)-asin(v[1] / g)
        else:
           u2 = 0

        DimensionCurve.rotation_euler[0] = radians(self.Dimension_rotation)
        DimensionCurve.rotation_euler[1] = u1
        DimensionCurve.rotation_euler[2] = u2

    # Align to view
    if self.Dimension_align_to_camera :
        obj_camera = bpy.context.scene.camera
        DimensionCurve.rotation_euler[0] = obj_camera.rotation_euler[0]
        DimensionCurve.rotation_euler[1] = obj_camera.rotation_euler[1]
        DimensionCurve.rotation_euler[2] = obj_camera.rotation_euler[2]

    # set materials
    if self.Dimension_matname in bpy.data.materials :
        setMaterial(DimensionCurve, bpy.data.materials[self.Dimension_matname])
        setMaterial(DimensionText, bpy.data.materials[self.Dimension_matname])
    else:
        red = makeMaterial(self.Dimension_matname, (1, 0, 0), (1, 0, 0), 1)
        setMaterial(DimensionCurve, red)
        setMaterial(DimensionText, red)

    setBezierHandles(DimensionCurve, 'VECTOR')
    setBezierHandles(DimensionText, 'VECTOR')

    group_name = 'Dimensions'

    bpy.ops.object.mode_set(mode = 'OBJECT')

    if group_name in bpy.data.collections:
        group = bpy.data.collections[group_name]
    else:
        group = bpy.data.collections.new(group_name)

    if not DimensionCurve.name in group.objects:
        group.objects.link(DimensionCurve)

    if not DimensionText.name in group.objects:
        group.objects.link(DimensionText)

    DimensionText.parent = DimensionCurve

    if self.Dimension_appoint_parent and not self.Dimension_parent == '':
        const =  DimensionCurve.constraints.new(type='CHILD_OF')
        const.target =  bpy.data.objects[self.Dimension_parent]
        const.inverse_matrix = bpy.data.objects[self.Dimension_parent].matrix_world.inverted()
        bpy.context.scene.update()

    bpy.ops.object.select_all(action='DESELECT')
    DimensionCurve.select = True
    DimensionText.select = True
    bpy.context.scene.objects.active = DimensionCurve
    bpy.context.scene.update()

    DimensionCurve.Dimension_Name = self.Dimension_Name
    DimensionCurve.Dimension_Type = self.Dimension_Type
    DimensionCurve.Dimension_XYZType = self.Dimension_XYZType
    DimensionCurve.Dimension_XYType = self.Dimension_XYType
    DimensionCurve.Dimension_XZType = self.Dimension_XZType
    DimensionCurve.Dimension_YZType = self.Dimension_YZType
    DimensionCurve.Dimension_startlocation = c
    DimensionCurve.Dimension_endlocation = self.Dimension_endlocation
    DimensionCurve.Dimension_endanglelocation = self.Dimension_endanglelocation
    DimensionCurve.Dimension_width_or_location = self.Dimension_width_or_location
    DimensionCurve.Dimension_liberty = self.Dimension_liberty
    DimensionCurve.Dimension_Change = False

    #### Dimension properties
    DimensionCurve.Dimension_resolution = self.Dimension_resolution
    DimensionCurve.Dimension_width = self.Dimension_width
    DimensionCurve.Dimension_length = self.Dimension_length
    DimensionCurve.Dimension_dsize = self.Dimension_dsize
    DimensionCurve.Dimension_depth = self.Dimension_depth
    DimensionCurve.Dimension_depth_from_center = self.Dimension_depth_from_center
    DimensionCurve.Dimension_angle = self.Dimension_angle
    DimensionCurve.Dimension_rotation = self.Dimension_rotation
    DimensionCurve.Dimension_offset = self.Dimension_offset

    #### Dimension text properties
    DimensionCurve.Dimension_textsize = self.Dimension_textsize
    DimensionCurve.Dimension_textdepth = self.Dimension_textdepth
    DimensionCurve.Dimension_textround = self.Dimension_textround
    DimensionCurve.Dimension_font = self.Dimension_font

    #### Dimension Arrow properties
    DimensionCurve.Dimension_arrow = self.Dimension_arrow
    DimensionCurve.Dimension_arrowdepth = self.Dimension_arrowdepth
    DimensionCurve.Dimension_arrowlength = self.Dimension_arrowlength

    #### Materials properties
    DimensionCurve.Dimension_matname = self.Dimension_matname

    #### Note properties
    DimensionCurve.Dimension_note = self.Dimension_note
    DimensionCurve.Dimension_align_to_camera = self.Dimension_align_to_camera

    #### Parent
    DimensionCurve.Dimension_parent = self.Dimension_parent
    DimensionCurve.Dimension_appoint_parent = self.Dimension_appoint_parent

    #### Units
    DimensionCurve.Dimension_units = self.Dimension_units
    DimensionCurve.Dimension_add_units_name = self.Dimension_add_units_name

    return

##------------------------------------------------------------
# Main Function
def main(self, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action = 'DESELECT')

    # options
    Type = self.Dimension_Type

    if self.Dimension_width_or_location == 'location':
        if self.Dimension_liberty == '2D':
            if self.Dimension_XYZType == 'TOP':
                if self.Dimension_XYType == 'X':
                    self.Dimension_width = self.Dimension_endlocation[0] - self.Dimension_startlocation[0]
                if self.Dimension_XYType == 'Y':
                    self.Dimension_width = self.Dimension_endlocation[1] - self.Dimension_startlocation[1]
            if self.Dimension_XYZType == 'FRONT':
                if self.Dimension_XZType == 'X':
                    self.Dimension_width = self.Dimension_endlocation[0] - self.Dimension_startlocation[0]
                if self.Dimension_XZType == 'Z':
                    self.Dimension_width = self.Dimension_endlocation[2] - self.Dimension_startlocation[2]
            if self.Dimension_XYZType == 'RIGHT':
                if self.Dimension_YZType == 'Y':
                    self.Dimension_width = self.Dimension_endlocation[1] - self.Dimension_startlocation[1]
                if self.Dimension_YZType == 'Z':
                    self.Dimension_width = self.Dimension_endlocation[2] - self.Dimension_startlocation[2]
            if self.Dimension_XYZType == 'BOTTOM':
                if self.Dimension_XYType == 'X':
                    self.Dimension_width = self.Dimension_endlocation[0] - self.Dimension_startlocation[0]
                if self.Dimension_XYType == 'Y':
                    self.Dimension_width = self.Dimension_endlocation[1] - self.Dimension_startlocation[1]
            if self.Dimension_XYZType == 'BACK':
                if self.Dimension_XZType == 'X':
                    self.Dimension_width = self.Dimension_endlocation[0] - self.Dimension_startlocation[0]
                if self.Dimension_XZType == 'Z':
                    self.Dimension_width = self.Dimension_endlocation[2] - self.Dimension_startlocation[2]
            if self.Dimension_XYZType == 'LEFT':
                if self.Dimension_YZType == 'Y':
                    self.Dimension_width = self.Dimension_endlocation[1] - self.Dimension_startlocation[1]
                if self.Dimension_YZType == 'Z':
                    self.Dimension_width = self.Dimension_endlocation[2] - self.Dimension_startlocation[2]
        if self.Dimension_liberty == '3D':
            v = self.Dimension_endlocation - self.Dimension_startlocation
            self.Dimension_width = v.length

        if Type == 'Angular1' or Type == 'Angular2' or Type == 'Angular3':
            c = ablength(self.Dimension_startlocation.x, self.Dimension_startlocation.y, self.Dimension_startlocation.z, self.Dimension_endlocation.x, self.Dimension_endlocation.y, self.Dimension_endlocation.z)
            b = ablength(self.Dimension_startlocation.x, self.Dimension_startlocation.y, self.Dimension_startlocation.z, self.Dimension_endanglelocation.x, self.Dimension_endanglelocation.y, self.Dimension_endanglelocation.z)
            a = ablength(self.Dimension_endanglelocation.x, self.Dimension_endanglelocation.y, self.Dimension_endanglelocation.z, self.Dimension_endlocation.x, self.Dimension_endlocation.y, self.Dimension_endlocation.z)
            self.Dimension_width = max(a, b, c)
            vanglex = self.Dimension_endanglelocation.x - self.Dimension_startlocation.x
            vangley = self.Dimension_endanglelocation.y - self.Dimension_startlocation.y
            vanglez = self.Dimension_endanglelocation.z - self.Dimension_startlocation.z
            vendx = self.Dimension_endlocation.x - self.Dimension_startlocation.x
            vendy = self.Dimension_endlocation.y - self.Dimension_startlocation.y
            vendz = self.Dimension_endlocation.z - self.Dimension_startlocation.z
            if self.Dimension_XYZType == 'TOP' or self.Dimension_XYZType == 'BOTTOM':
                self.Dimension_XYType = 'X'
                g = hypot(vanglex, vangley)
                if g !=  0 :
                   u2 = acos(vanglex / g)
                   u1 = asin(vangley / g)
                   if u1 < 0 :
                       u2 = -u2
                else:
                   u2 = 0
                g = hypot(vendx, vendy)
                if g !=  0 :
                   uu2 = acos(vendx / g)
                   uu1 = asin(vendy / g)
                   if uu1 < 0 :
                       uu2 = -uu2
                else:
                   uu2 = 0
                self.Dimension_angle = degrees(u2 - uu2)
            if self.Dimension_XYZType == 'FRONT' or self.Dimension_XYZType == 'BACK':
                self.Dimension_XZType = 'Z'
                g = hypot(vanglex, vanglez)
                if g !=  0 :
                   u2 = acos(vanglex / g)
                   u1 = asin(vanglez / g)
                   if u1 < 0 :
                       u2 = -u2
                else:
                   u2 = 0
                g = hypot(vendx, vendz)
                if g !=  0 :
                   uu2 = acos(vendx / g)
                   uu1 = asin(vendz / g)
                   if uu1 < 0 :
                       uu2 = -uu2
                else:
                   uu2 = 0
                self.Dimension_angle = degrees(u2 - uu2)
            if self.Dimension_XYZType == 'RIGHT' or self.Dimension_XYZType == 'LEFT':
                self.Dimension_YZType = 'Z'
                g = hypot(vangley, vanglez)
                if g !=  0 :
                   u2 = acos(vangley / g)
                   u1 = asin(vanglez / g)
                   if u1 < 0 :
                       u2 = -u2
                else:
                   u2 = 0
                g = hypot(vendy, vendz)
                if g !=  0 :
                   uu2 = acos(vendy / g)
                   uu1 = asin(vendz / g)
                   if uu1 < 0 :
                       uu2 = -uu2
                else:
                   uu2 = 0
                self.Dimension_angle = degrees(u2 - uu2)
            if self.Dimension_liberty == '3D':
                c = ablength(self.Dimension_startlocation.x, self.Dimension_startlocation.y, self.Dimension_startlocation.z, self.Dimension_endlocation.x, self.Dimension_endlocation.y, self.Dimension_endlocation.z)
                b = ablength(self.Dimension_startlocation.x, self.Dimension_startlocation.y, self.Dimension_startlocation.z, self.Dimension_endanglelocation.x, self.Dimension_endanglelocation.y, self.Dimension_endanglelocation.z)
                a = ablength(self.Dimension_endanglelocation.x, self.Dimension_endanglelocation.y, self.Dimension_endanglelocation.z, self.Dimension_endlocation.x, self.Dimension_endlocation.y, self.Dimension_endlocation.z)
                if b != 0 and c != 0 :
                    self.Dimension_angle = degrees(acos((b**2 + c**2 - a**2)/(2*b*c)))
                else:
                    self.Dimension_angle = 0

    #
    if self.Dimension_width == 0:
        return {'FINISHED'}

    # get verts
    if Type == 'Linear-1':
        verts = Linear1(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_dsize,
                          self.Dimension_depth,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Linear-2':
        verts = Linear2(self.Dimension_width,
                          self.Dimension_dsize,
                          self.Dimension_depth,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Linear-3':
        verts = Linear3(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_dsize,
                          self.Dimension_depth,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Radius':
        verts = Radius(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_dsize,
                          self.Dimension_depth,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Diameter':
        verts = Diameter(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_dsize,
                          self.Dimension_depth,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Angular1':
        if self.Dimension_angle == 0:
            return {'FINISHED'}
        verts = Angular1(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_depth,
                          self.Dimension_angle,
                          self.Dimension_resolution,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Angular2':
        if self.Dimension_angle == 0:
            return {'FINISHED'}
        verts = Angular2(self.Dimension_width,
                          self.Dimension_depth,
                          self.Dimension_angle,
                          self.Dimension_resolution,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Angular3':
        if self.Dimension_angle == 0:
            return {'FINISHED'}
        verts = Angular3(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_dsize,
                          self.Dimension_depth,
                          self.Dimension_angle,
                          self.Dimension_resolution,
                          self.Dimension_depth_from_center,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    if Type == 'Note':
        verts = Note(self.Dimension_width,
                          self.Dimension_length,
                          self.Dimension_depth,
                          self.Dimension_angle,
                          self.Dimension_arrow,
                          self.Dimension_arrowdepth,
                          self.Dimension_arrowlength)

    vertArray = []
    # turn verts into array
    for v in verts:
        vertArray  += v

    # create object
    createCurve(vertArray, self, align_matrix)

    return

#### Delete dimension group
def DimensionDelete(self, context):

    bpy.context.scene.update()
    bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
    bpy.ops.object.delete()
    bpy.context.scene.update()

    return

class Dimension(bpy.types.Operator):
    ''''''
    bl_idname = "curve.dimension"
    bl_label = "Dimension"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "add dimension"

    # align_matrix for the invoke
    align_matrix = Matrix()

    Dimension = BoolProperty(name = "Dimension",
                default = True,
                description = "dimension")

    #### change properties
    Dimension_Name = StringProperty(name = "Name",
                    description = "Name")

    Dimension_Change = BoolProperty(name = "Change",
                default = False,
                description = "change dimension")

    Dimension_Delete = StringProperty(name = "Delete",
                    description = "Delete dimension")

    #### general properties
    Types = [('Linear-1', 'Linear-1', 'Linear-1'),
             ('Linear-2', 'Linear-2', 'Linear-2'),
             ('Linear-3', 'Linear-3', 'Linear-3'),
             ('Radius', 'Radius', 'Radius'),
             ('Diameter', 'Diameter', 'Diameter'),
             ('Angular1', 'Angular1', 'Angular1'),
             ('Angular2', 'Angular2', 'Angular2'),
             ('Angular3', 'Angular3', 'Angular3'),
             ('Note', 'Note', 'Note')]
    Dimension_Type = EnumProperty(name = "Type",
                description = "Form of Curve to create",
                items = Types)
    XYZTypes = [
                ('TOP', 'Top', 'TOP'),
                ('FRONT', 'Front', 'FRONT'),
                ('RIGHT', 'Right', 'RIGHT'),
                ('BOTTOM', 'Bottom', 'BOTTOM'),
                ('BACK', 'Back', 'BACK'),
                ('LEFT', 'Left', 'LEFT')]
    Dimension_XYZType = EnumProperty(name = "Coordinate system",
                description = "Place in a coordinate system",
                items = XYZTypes)
    XYTypes = [
                ('X', 'X', 'X'),
                ('Y', 'Y', 'Y')]
    Dimension_XYType = EnumProperty(name = "XY",
                description = "XY",
                items = XYTypes)
    XZTypes = [
                ('X', 'X', 'X'),
                ('Z', 'Z', 'Z')]
    Dimension_XZType = EnumProperty(name = "XZ",
                description = "XZ",
                items = XZTypes)
    YZTypes = [
                ('Y', 'Y', 'Y'),
                ('Z', 'Z', 'Z')]
    Dimension_YZType = EnumProperty(name = "YZ",
                description = "YZ",
                items = YZTypes)
    Dimension_startlocation = FloatVectorProperty(name = "",
                description = "Start location",
                default = (0.0, 0.0, 0.0),
                subtype = 'XYZ')
    Dimension_endlocation = FloatVectorProperty(name = "",
                description = "End location",
                default = (2.0, 2.0, 2.0),
                subtype = 'XYZ')
    Dimension_endanglelocation = FloatVectorProperty(name = "",
                description = "End angle location",
                default = (4.0, 4.0, 4.0),
                subtype = 'XYZ')
    width_or_location_items = [
                ('width', 'width', 'width'),
                ('location', 'location', 'location')]
    Dimension_width_or_location = EnumProperty(name = "width or location",
                items = width_or_location_items,
                description = "width or location")
    libertyItems = [
                ('2D', '2D', '2D'),
                ('3D', '3D', '3D')]
    Dimension_liberty = EnumProperty(name = "2D / 3D",
                items = libertyItems,
                description = "2D or 3D Dimension")

    ### Arrow
    Arrows = [
                ('Arrow1', 'Arrow1', 'Arrow1'),
                ('Arrow2', 'Arrow2', 'Arrow2'),
                ('Serifs1', 'Serifs1', 'Serifs1'),
                ('Serifs2', 'Serifs2', 'Serifs2'),
                ('Without', 'Without', 'Without')]
    Dimension_arrow = EnumProperty(name = "Arrow",
                items = Arrows,
                description = "Arrow")
    Dimension_arrowdepth = FloatProperty(name = "Depth",
                default = 0.1,
                min = 0, soft_min = 0,
                description = "Arrow depth")
    Dimension_arrowlength = FloatProperty(name = "Length",
                default = 0.25,
                min = 0, soft_min = 0,
                description = "Arrow length")

    #### Dimension properties
    Dimension_resolution = IntProperty(name = "Resolution",
                default = 10,
                min = 1, soft_min = 1,
                description = "Resolution")
    Dimension_width = FloatProperty(name = "Width",
                default = 2,
                unit = 'LENGTH',
                description = "Width")
    Dimension_length = FloatProperty(name = "Length",
                default = 2,
                description = "Length")
    Dimension_dsize = FloatProperty(name = "Size",
                default = 1,
                min = 0, soft_min = 0,
                description = "Size")
    Dimension_depth = FloatProperty(name = "Depth",
                default = 0.1,
                min = 0, soft_min = 0,
                description = "Depth")
    Dimension_depth_from_center = BoolProperty(name = "Depth from center",
                default = False,
                description = "Depth from center")
    Dimension_angle = FloatProperty(name = "Angle",
                default = 45,
                description = "Angle")
    Dimension_rotation = FloatProperty(name = "Rotation",
                default = 0,
                description = "Rotation")
    Dimension_offset = FloatProperty(name = "Offset",
                default = 0,
                description = "Offset")

    #### Dimension units properties
    Units = [
                ('None', 'None', 'None'),
                ('\u00b5m', '\u00b5m', '\u00b5m'),
                ('mm', 'mm', 'mm'),
                ('cm', 'cm', 'cm'),
                ('m', 'm', 'm'),
                ('km', 'km', 'km'),
                ('thou', 'thou', 'thou'),
                ('"', '"', '"'),
                ('\'', '\'', '\''),
                ('yd', 'yd', 'yd'),
                ('mi', 'mi', 'mi')]
    Dimension_units = EnumProperty(name = "Units",
                items = Units,
                description = "Units")
    Dimension_add_units_name = BoolProperty(name = "Add units name",
                default = False,
                description = "Add units name")

    #### Dimension text properties
    Dimension_textsize = FloatProperty(name = "Size",
                default = 1,
                description = "Size")
    Dimension_textdepth = FloatProperty(name = "Depth",
                default = 0.2,
                description = "Depth")
    Dimension_textround = IntProperty(name = "Rounding",
                default = 2,
                min = 0, soft_min = 0,
                description = "Rounding")
    Dimension_font = StringProperty(name = "Font",
                default = '',
                subtype = 'FILE_PATH',
                description = "Font")

    #### Materials properties
    Dimension_matname = StringProperty(name = "Name",
                default = 'Dimension_Red',
                description = "Material name")

    #### Note properties
    Dimension_note = StringProperty(name = "Note",
                default = 'Note',
                description = "Note text")
    Dimension_align_to_camera = BoolProperty(name = "Align to camera",
                default = False,
                description = "Align to camera")

    TMP_startlocation = FloatVectorProperty(name = "",
                description = "Start location",
                default = (0.0, 0.0, 0.0),
                subtype = 'XYZ')
    TMP_endlocation = FloatVectorProperty(name = "",
                description = "Start location",
                default = (2.0, 2.0, 2.0),
                subtype = 'XYZ')
    TMP_endanglelocation = FloatVectorProperty(name = "",
                description = "Start location",
                default = (4.0, 4.0, 4.0),
                subtype = 'XYZ')
    #### Parent
    Dimension_parent = StringProperty(name = "Parent",
                default = '',
                description = "Parent")
    Dimension_appoint_parent = BoolProperty(name = "Appoint parent",
                default = False,
                description = "Appoint parent")

    ##### DRAW #####
    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, 'Dimension_Type')

        # options per Type Linear-1(width = 2, length = 2, dsize = 1, depth = 0.1)
        if self.Dimension_Type == 'Linear-1':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_width')
            else:
                row.prop(self, 'Dimension_endlocation')
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_dsize')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_depth_from_center')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_offset')

        # options per Type Linear-2(width = 2, dsize = 1, depth = 0.1)
        if self.Dimension_Type == 'Linear-2':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_width')
            else:
                row.prop(self, 'Dimension_endlocation')
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_dsize')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_offset')

        # options per Type Linear-3(width = 2, length = 2, dsize = 1, depth = 0.1)
        if self.Dimension_Type == 'Linear-3':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_width')
            else:
                row.prop(self, 'Dimension_endlocation')
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_dsize')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_depth_from_center')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_offset')

        # options per Type Radius(width = 2, length = 2, dsize = 1, depth = 0.1)
        if self.Dimension_Type == 'Radius':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_width')
            else:
                row.prop(self, 'Dimension_endlocation')
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_dsize')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_rotation')

        # options per Type Diameter(width = 2, length = 2, dsize = 1, depth = 0.1)
        if self.Dimension_Type == 'Diameter':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_width')
            else:
                row.prop(self, 'Dimension_endlocation')
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_dsize')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_rotation')

        # options per Type Angular1(width = 2, dsize = 1, depth = 0.1, angle = 45)
        if self.Dimension_Type == 'Angular1':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_angle')
            else:
                row.prop(self, 'Dimension_endlocation')
                col = layout.column()
                col.label(text = "End angle location:")
                row = layout.row()
                row.prop(self, 'Dimension_endanglelocation')
                row = layout.row()
                props = row.operator("curve.dimension", text = 'Change angle')
                props.Dimension_Change = True
                props.Dimension_Delete = self.Dimension_Name
                props.Dimension_width_or_location = self.Dimension_width_or_location
                props.Dimension_startlocation = self.Dimension_endanglelocation
                props.Dimension_endlocation = self.Dimension_startlocation
                props.Dimension_endanglelocation = self.Dimension_endlocation
                props.Dimension_liberty = self.Dimension_liberty
                props.Dimension_Type = self.Dimension_Type
                props.Dimension_XYZType = self.Dimension_XYZType
                props.Dimension_XYType = self.Dimension_XYType
                props.Dimension_XZType = self.Dimension_XZType
                props.Dimension_YZType = self.Dimension_YZType
                props.Dimension_resolution = self.Dimension_resolution
                props.Dimension_width = self.Dimension_width
                props.Dimension_length = self.Dimension_length
                props.Dimension_dsize = self.Dimension_dsize
                props.Dimension_depth = self.Dimension_depth
                props.Dimension_depth_from_center = self.Dimension_depth_from_center
                props.Dimension_angle = self.Dimension_angle
                props.Dimension_rotation = self.Dimension_rotation
                props.Dimension_offset = self.Dimension_offset
                props.Dimension_textsize = self.Dimension_textsize
                props.Dimension_textdepth = self.Dimension_textdepth
                props.Dimension_textround = self.Dimension_textround
                props.Dimension_matname = self.Dimension_matname
                props.Dimension_note = self.Dimension_note
                props.Dimension_align_to_camera = self.Dimension_align_to_camera
                props.Dimension_arrow = self.Dimension_arrow
                props.Dimension_arrowdepth = self.Dimension_arrowdepth
                props.Dimension_arrowlength = self.Dimension_arrowlength
                props.Dimension_parent = self.Dimension_parent
                props.Dimension_appoint_parent = self.Dimension_appoint_parent
                props.Dimension_units = self.Dimension_units
                props.Dimension_add_units_name = self.Dimension_add_units_name
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_width')
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_depth_from_center')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_resolution')

        # options per Type Angular2(width = 2, dsize = 1, depth = 0.1, angle = 45)
        if self.Dimension_Type == 'Angular2':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_angle')
            else:
                row.prop(self, 'Dimension_endlocation')
                col = layout.column()
                col.label(text = "End angle location:")
                row = layout.row()
                row.prop(self, 'Dimension_endanglelocation')
                row = layout.row()
                props = row.operator("curve.dimension", text = 'Change angle')
                props.Dimension_Change = True
                props.Dimension_Delete = self.Dimension_Name
                props.Dimension_width_or_location = self.Dimension_width_or_location
                props.Dimension_startlocation = self.Dimension_endanglelocation
                props.Dimension_endlocation = self.Dimension_startlocation
                props.Dimension_endanglelocation = self.Dimension_endlocation
                props.Dimension_liberty = self.Dimension_liberty
                props.Dimension_Type = self.Dimension_Type
                props.Dimension_XYZType = self.Dimension_XYZType
                props.Dimension_XYType = self.Dimension_XYType
                props.Dimension_XZType = self.Dimension_XZType
                props.Dimension_YZType = self.Dimension_YZType
                props.Dimension_resolution = self.Dimension_resolution
                props.Dimension_width = self.Dimension_width
                props.Dimension_length = self.Dimension_length
                props.Dimension_dsize = self.Dimension_dsize
                props.Dimension_depth = self.Dimension_depth
                props.Dimension_depth_from_center = self.Dimension_depth_from_center
                props.Dimension_angle = self.Dimension_angle
                props.Dimension_rotation = self.Dimension_rotation
                props.Dimension_offset = self.Dimension_offset
                props.Dimension_textsize = self.Dimension_textsize
                props.Dimension_textdepth = self.Dimension_textdepth
                props.Dimension_textround = self.Dimension_textround
                props.Dimension_matname = self.Dimension_matname
                props.Dimension_note = self.Dimension_note
                props.Dimension_align_to_camera = self.Dimension_align_to_camera
                props.Dimension_arrow = self.Dimension_arrow
                props.Dimension_arrowdepth = self.Dimension_arrowdepth
                props.Dimension_arrowlength = self.Dimension_arrowlength
                props.Dimension_parent = self.Dimension_parent
                props.Dimension_appoint_parent = self.Dimension_appoint_parent
                props.Dimension_units = self.Dimension_units
                props.Dimension_add_units_name = self.Dimension_add_units_name
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_width')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_resolution')

        # options per Type Angular3(width = 2, dsize = 1, depth = 0.1, angle = 45)
        if self.Dimension_Type == 'Angular3':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_angle')
            else:
                row.prop(self, 'Dimension_endlocation')
                col = layout.column()
                col.label(text = "End angle location:")
                row = layout.row()
                row.prop(self, 'Dimension_endanglelocation')
                row = layout.row()
                props = row.operator("curve.dimension", text = 'Change angle')
                props.Dimension_Change = True
                props.Dimension_Delete = self.Dimension_Name
                props.Dimension_width_or_location = self.Dimension_width_or_location
                props.Dimension_startlocation = self.Dimension_endanglelocation
                props.Dimension_endlocation = self.Dimension_startlocation
                props.Dimension_endanglelocation = self.Dimension_endlocation
                props.Dimension_liberty = self.Dimension_liberty
                props.Dimension_Type = self.Dimension_Type
                props.Dimension_XYZType = self.Dimension_XYZType
                props.Dimension_XYType = self.Dimension_XYType
                props.Dimension_XZType = self.Dimension_XZType
                props.Dimension_YZType = self.Dimension_YZType
                props.Dimension_resolution = self.Dimension_resolution
                props.Dimension_width = self.Dimension_width
                props.Dimension_length = self.Dimension_length
                props.Dimension_dsize = self.Dimension_dsize
                props.Dimension_depth = self.Dimension_depth
                props.Dimension_depth_from_center = self.Dimension_depth_from_center
                props.Dimension_angle = self.Dimension_angle
                props.Dimension_rotation = self.Dimension_rotation
                props.Dimension_offset = self.Dimension_offset
                props.Dimension_textsize = self.Dimension_textsize
                props.Dimension_textdepth = self.Dimension_textdepth
                props.Dimension_textround = self.Dimension_textround
                props.Dimension_matname = self.Dimension_matname
                props.Dimension_note = self.Dimension_note
                props.Dimension_align_to_camera = self.Dimension_align_to_camera
                props.Dimension_arrow = self.Dimension_arrow
                props.Dimension_arrowdepth = self.Dimension_arrowdepth
                props.Dimension_arrowlength = self.Dimension_arrowlength
                props.Dimension_parent = self.Dimension_parent
                props.Dimension_appoint_parent = self.Dimension_appoint_parent
                props.Dimension_units = self.Dimension_units
                props.Dimension_add_units_name = self.Dimension_add_units_name
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_width')
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_dsize')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_depth_from_center')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_resolution')

        # options per Type Note(width = 2, length = 2, dsize = 1, depth = 0.1)
        if self.Dimension_Type == 'Note':
            row = layout.row()
            row.prop(self, 'Dimension_width_or_location', expand = True)
            col = layout.column()
            col.label(text = "End location:")
            row = layout.row()
            if self.Dimension_width_or_location == 'width':
                row.prop(self, 'Dimension_width')
            else:
                row.prop(self, 'Dimension_endlocation')
            box = layout.box()
            box.label("Options")
            box.prop(self, 'Dimension_length')
            box.prop(self, 'Dimension_depth')
            box.prop(self, 'Dimension_angle')
            box.prop(self, 'Dimension_rotation')
            box.prop(self, 'Dimension_note')
            box.prop(self, 'Dimension_offset')

        col = layout.column()
        row = layout.row()
        row.prop(self, 'Dimension_align_to_camera')
        col = layout.column()
        row = layout.row()
        row.prop(self, 'Dimension_liberty', expand = True)

        if self.Dimension_liberty == '2D':
            col = layout.column()
            col.label("Coordinate system")
            row = layout.row()
            row.prop(self, 'Dimension_XYZType', expand = True)
            if self.Dimension_XYZType == 'TOP' or self.Dimension_XYZType == 'BOTTOM':
                row = layout.row()
                row.prop(self, 'Dimension_XYType', expand = True)
            if self.Dimension_XYZType == 'FRONT' or self.Dimension_XYZType == 'BACK':
                row = layout.row()
                row.prop(self, 'Dimension_XZType', expand = True)
            if self.Dimension_XYZType == 'RIGHT' or self.Dimension_XYZType == 'LEFT':
                row = layout.row()
                row.prop(self, 'Dimension_YZType', expand = True)

        col = layout.column()
        col.label("Start location:")
        row = layout.row()
        row.prop(self, 'Dimension_startlocation')

        box = layout.box()
        box.prop(self, 'Dimension_units')
        box.prop(self, 'Dimension_add_units_name')

        if not self.Dimension_parent == '':
            box = layout.box()
            box.prop(self, 'Dimension_appoint_parent')

        box = layout.box()
        box.label("Text Options")
        box.prop(self, 'Dimension_textsize')
        box.prop(self, 'Dimension_textdepth')
        box.prop(self, 'Dimension_textround')
        box.prop(self, 'Dimension_font')

        box = layout.box()
        box.label("Arrow Options")
        box.prop(self, 'Dimension_arrow')
        box.prop(self, 'Dimension_arrowdepth')
        box.prop(self, 'Dimension_arrowlength')

        box = layout.box()
        box.label("Material Option")
        box.prop(self, 'Dimension_matname')

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene !=  None

    ##### EXECUTE #####
    def execute(self, context):

        if self.Dimension_Change:
            DimensionDelete(self, context)

        #go to object mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.context.scene.update()

        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        # main function
        self.align_matrix = align_matrix(context, self.Dimension_startlocation)
        main(self, self.align_matrix)

        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        bpy.context.scene.update()
        if self.Dimension_Change:
            bpy.context.scene.cursor_location = self.Dimension_startlocation
        else:
            if self.Dimension_width_or_location == 'width':
                self.Dimension_startlocation = bpy.context.scene.cursor_location

            if self.Dimension_width_or_location == 'location':
                if (self.Dimension_endlocation[2] - self.Dimension_startlocation[2]) !=  0 :
                    self.Dimension_XYZType = 'FRONT'
                    self.Dimension_XZType = 'Z'
                if (self.Dimension_endlocation[1] - self.Dimension_startlocation[1]) !=  0 :
                    self.Dimension_XYZType = 'TOP'
                    self.Dimension_XYType = 'Y'
                if (self.Dimension_endlocation[0] - self.Dimension_startlocation[0]) !=  0 :
                    self.Dimension_XYZType = 'TOP'
                    self.Dimension_XYType = 'X'

        self.align_matrix = align_matrix(context, self.Dimension_startlocation)

        self.execute(context)

        return {'FINISHED'}

# Properties class
class DimensionAdd(bpy.types.Panel):
    ''''''
    bl_idname = "VIEW3D_PT_properties_dimension_add"
    bl_label = "Dimension Add"
    bl_description = "Dimension Add"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        selected = 0
        for obj in context.selected_objects :
            if obj.type == 'MESH':
                for i in obj.data.vertices :
                    if i.select :
                        selected  += 1

            if obj.type == 'CURVE':
                for i in obj.data.splines :
                    for j in i.bezier_points :
                        if j.select_control_point :
                            selected  += 1

        if selected == 1 or selected == 2 or selected == 3:
            return context.selected_objects

    ##### DRAW #####
    def draw(self, context):
        vertex = []
        for obj in context.selected_objects :
            if obj.type == 'MESH':
                for i in obj.data.vertices :
                    if i.select :
                        vertex.append(obj.matrix_world * i.co)

            if obj.type == 'CURVE':
                for i in obj.data.splines :
                    for j in i.bezier_points :
                        if j.select_control_point :
                            vertex.append(obj.matrix_world * j.co)

        if len(vertex) == 1:
            startvertex = vertex[0]
            endvertex = bpy.context.scene.cursor_location
            layout = self.layout
            col = layout.column()
            col.label("Note:")
            row = layout.row()
            props1 = row.operator("curve.dimension", text = 'Add linear note')
            props1.Dimension_Change = False
            props1.Dimension_Type = 'Note'
            props1.Dimension_width_or_location = 'location'
            props1.Dimension_startlocation = startvertex
            props1.Dimension_liberty = '2D'
            props1.Dimension_rotation = 0
            props1.Dimension_parent = obj.name

            props2 = row.operator("curve.dimension", text = 'Add 3D note')
            props2.Dimension_Change = False
            props2.Dimension_Type = 'Note'
            props2.Dimension_width_or_location = 'location'
            props2.Dimension_startlocation = startvertex
            props2.Dimension_liberty = '3D'
            props2.Dimension_rotation = 0
            props2.Dimension_parent = obj.name

            col = layout.column()
            col.label("Distance to 3D cursor:")
            row = layout.row()
            props3 = row.operator("curve.dimension", text = 'Add linear dimension')
            props3.Dimension_Change = False
            props3.Dimension_Type = 'Linear-1'
            props3.Dimension_width_or_location = 'location'
            props3.Dimension_startlocation = endvertex
            props3.Dimension_endlocation = startvertex
            props3.Dimension_liberty = '2D'
            props3.Dimension_rotation = 0
            props3.Dimension_parent = obj.name

            props4 = row.operator("curve.dimension", text = 'Add 3D dimension')
            props4.Dimension_Change = False
            props4.Dimension_Type = 'Linear-1'
            props4.Dimension_width_or_location = 'location'
            props4.Dimension_startlocation = endvertex
            props4.Dimension_endlocation = startvertex
            props4.Dimension_liberty = '3D'
            props4.Dimension_rotation = 0
            props4.Dimension_parent = obj.name

            col = layout.column()
            col.label("Radius to 3D cursor:")
            row = layout.row()
            props7 = row.operator("curve.dimension", text = 'Add linear radius')
            props7.Dimension_Change = False
            props7.Dimension_Type = 'Radius'
            props7.Dimension_width_or_location = 'location'
            props7.Dimension_startlocation = endvertex
            props7.Dimension_endlocation = startvertex
            props7.Dimension_liberty = '2D'
            props7.Dimension_rotation = 0
            props7.Dimension_parent = obj.name

            props8 = row.operator("curve.dimension", text = 'Add 3D radius')
            props8.Dimension_Change = False
            props8.Dimension_Type = 'Radius'
            props8.Dimension_width_or_location = 'location'
            props8.Dimension_startlocation = endvertex
            props8.Dimension_endlocation = startvertex
            props8.Dimension_liberty = '3D'
            props8.Dimension_rotation = 0
            props8.Dimension_parent = obj.name

            col = layout.column()
            col.label("Diameter to 3D cursor:")
            row = layout.row()
            props9 = row.operator("curve.dimension", text = 'Add linear diameter')
            props9.Dimension_Change = False
            props9.Dimension_Type = 'Diameter'
            props9.Dimension_width_or_location = 'location'
            props9.Dimension_startlocation = endvertex
            props9.Dimension_endlocation = startvertex
            props9.Dimension_liberty = '2D'
            props9.Dimension_rotation = 0
            props9.Dimension_parent = obj.name

            props10 = row.operator("curve.dimension", text = 'Add 3D diameter')
            props10.Dimension_Change = False
            props10.Dimension_Type = 'Diameter'
            props10.Dimension_width_or_location = 'location'
            props10.Dimension_startlocation = endvertex
            props10.Dimension_endlocation = startvertex
            props10.Dimension_liberty = '3D'
            props10.Dimension_rotation = 0
            props10.Dimension_parent = obj.name

        if len(vertex) == 2:
            startvertex = vertex[0]
            endvertex = vertex[1]
            if endvertex[0] < startvertex[0]:
                startvertex = vertex[1]
                endvertex = vertex[0]

            layout = self.layout
            col = layout.column()
            col.label("Distance:")
            row = layout.row()
            props1 = row.operator("curve.dimension", text = 'Add linear dimension')
            props1.Dimension_Change = False
            props1.Dimension_Type = 'Linear-1'
            props1.Dimension_width_or_location = 'location'
            props1.Dimension_startlocation = startvertex
            props1.Dimension_endlocation = endvertex
            props1.Dimension_liberty = '2D'
            props1.Dimension_rotation = 0
            props1.Dimension_parent = obj.name

            props2 = row.operator("curve.dimension", text = 'Add 3D dimension')
            props2.Dimension_Change = False
            props2.Dimension_Type = 'Linear-1'
            props2.Dimension_width_or_location = 'location'
            props2.Dimension_startlocation = startvertex
            props2.Dimension_endlocation = endvertex
            props2.Dimension_liberty = '3D'
            props2.Dimension_rotation = 0
            props2.Dimension_parent = obj.name

            col = layout.column()
            col.label("Radius:")
            row = layout.row()
            props3 = row.operator("curve.dimension", text = 'Add linear radius')
            props3.Dimension_Change = False
            props3.Dimension_Type = 'Radius'
            props3.Dimension_width_or_location = 'location'
            props3.Dimension_startlocation = startvertex
            props3.Dimension_endlocation = endvertex
            props3.Dimension_liberty = '2D'
            props3.Dimension_rotation = 0
            props3.Dimension_parent = obj.name

            props4 = row.operator("curve.dimension", text = 'Add 3D radius')
            props4.Dimension_Change = False
            props4.Dimension_Type = 'Radius'
            props4.Dimension_width_or_location = 'location'
            props4.Dimension_startlocation = startvertex
            props4.Dimension_endlocation = endvertex
            props4.Dimension_liberty = '3D'
            props4.Dimension_rotation = 0
            props4.Dimension_parent = obj.name

            col = layout.column()
            col.label("Diameter:")
            row = layout.row()
            props5 = row.operator("curve.dimension", text = 'Add linear diameter')
            props5.Dimension_Change = False
            props5.Dimension_Type = 'Diameter'
            props5.Dimension_width_or_location = 'location'
            props5.Dimension_startlocation = startvertex
            props5.Dimension_endlocation = endvertex
            props5.Dimension_liberty = '2D'
            props5.Dimension_rotation = 0
            props5.Dimension_parent = obj.name

            props6 = row.operator("curve.dimension", text = 'Add 3D diameter')
            props6.Dimension_Change = False
            props6.Dimension_Type = 'Diameter'
            props6.Dimension_width_or_location = 'location'
            props6.Dimension_startlocation = startvertex
            props6.Dimension_endlocation = endvertex
            props6.Dimension_liberty = '3D'
            props6.Dimension_rotation = 0
            props6.Dimension_parent = obj.name

        if len(vertex) == 3:
            startvertex = vertex[0]
            endvertex = vertex[1]
            endanglevertex = vertex[2]
            if endvertex[0] < startvertex[0]:
                startvertex = vertex[1]
                endvertex = vertex[0]

            layout = self.layout
            col = layout.column()
            col.label("Angle:")
            row = layout.row()
            props1 = row.operator("curve.dimension", text = 'Add Linear angle dimension')
            props1.Dimension_Change = False
            props1.Dimension_Type = 'Angular1'
            props1.Dimension_width_or_location = 'location'
            props1.Dimension_startlocation = startvertex
            props1.Dimension_endlocation = endvertex
            props1.Dimension_endanglelocation = endanglevertex
            props1.Dimension_liberty = '2D'
            props1.Dimension_rotation = 0
            props1.Dimension_parent = obj.name

            props2 = row.operator("curve.dimension", text = 'Add 3D angle dimension')
            props2.Dimension_Change = False
            props2.Dimension_Type = 'Angular1'
            props2.Dimension_width_or_location = 'location'
            props2.Dimension_startlocation = startvertex
            props2.Dimension_endlocation = endvertex
            props2.Dimension_endanglelocation = endanglevertex
            props2.Dimension_liberty = '3D'
            props2.Dimension_rotation = 0
            props2.Dimension_parent = obj.name

# Properties class
class DimensionPanel(bpy.types.Panel):
    ''''''
    bl_idname = "OBJECT_PT_properties_dimension"
    bl_label = "Dimension change"
    bl_description = "Dimension change"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.Dimension == True:
            return (context.object)

    ##### DRAW #####
    def draw(self, context):
        if context.object.Dimension == True:
            layout = self.layout

            obj = context.object
            row = layout.row()

            props = row.operator("curve.dimension", text = 'Change')
            props.Dimension_Change = True
            props.Dimension_Delete = obj.name
            props.Dimension_width_or_location = obj.Dimension_width_or_location
            props.Dimension_startlocation = obj.location
            props.Dimension_endlocation = obj.Dimension_endlocation
            props.Dimension_endanglelocation = obj.Dimension_endanglelocation
            props.Dimension_liberty = obj.Dimension_liberty
            props.Dimension_Type = obj.Dimension_Type
            props.Dimension_XYZType = obj.Dimension_XYZType
            props.Dimension_XYType = obj.Dimension_XYType
            props.Dimension_XZType = obj.Dimension_XZType
            props.Dimension_YZType = obj.Dimension_YZType
            props.Dimension_resolution = obj.Dimension_resolution
            props.Dimension_width = obj.Dimension_width
            props.Dimension_length = obj.Dimension_length
            props.Dimension_dsize = obj.Dimension_dsize
            props.Dimension_depth = obj.Dimension_depth
            props.Dimension_depth_from_center = obj.Dimension_depth_from_center
            props.Dimension_angle = obj.Dimension_angle
            props.Dimension_rotation = obj.Dimension_rotation
            props.Dimension_offset = 0
            props.Dimension_textsize = obj.Dimension_textsize
            props.Dimension_textdepth = obj.Dimension_textdepth
            props.Dimension_textround = obj.Dimension_textround
            props.Dimension_font = obj.Dimension_font
            props.Dimension_matname = obj.Dimension_matname
            props.Dimension_note = obj.Dimension_note
            props.Dimension_align_to_camera = obj.Dimension_align_to_camera
            props.Dimension_arrow = obj.Dimension_arrow
            props.Dimension_arrowdepth = obj.Dimension_arrowdepth
            props.Dimension_arrowlength = obj.Dimension_arrowlength
            props.Dimension_parent = obj.Dimension_parent
            props.Dimension_appoint_parent = obj.Dimension_appoint_parent
            props.Dimension_units = obj.Dimension_units
            props.Dimension_add_units_name = obj.Dimension_add_units_name

#location update
def StartLocationUpdate(self, context):

    bpy.context.scene.cursor_location = self.Dimension_startlocation

    return

# Add properties to objects
def DimensionVariables():

    bpy.types.Object.Dimension = bpy.props.BoolProperty()
    bpy.types.Object.Dimension_Change = bpy.props.BoolProperty()
    bpy.types.Object.Dimension_Name = bpy.props.StringProperty(name = "Name",
                description = "Name")
    #### general properties
    Types = [('Linear-1', 'Linear-1', 'Linear-1'),
             ('Linear-2', 'Linear-2', 'Linear-2'),
             ('Linear-3', 'Linear-3', 'Linear-3'),
             ('Radius', 'Radius', 'Radius'),
             ('Diameter', 'Diameter', 'Diameter'),
             ('Angular1', 'Angular1', 'Angular1'),
             ('Angular2', 'Angular2', 'Angular2'),
             ('Angular3', 'Angular3', 'Angular3'),
             ('Note', 'Note', 'Note')]
    bpy.types.Object.Dimension_Type = bpy.props.EnumProperty(name = "Type",
                description = "Form of Curve to create",
                items = Types)
    XYZTypes = [
                ('TOP', 'Top', 'TOP'),
                ('FRONT', 'Front', 'FRONT'),
                ('RIGHT', 'Right', 'RIGHT'),
                ('BOTTOM', 'Bottom', 'BOTTOM'),
                ('BACK', 'Back', 'BACK'),
                ('LEFT', 'Left', 'LEFT')]
    bpy.types.Object.Dimension_XYZType = bpy.props.EnumProperty(name = "Coordinate system",
                description = "Place in a coordinate system",
                items = XYZTypes)
    XYTypes = [
                ('X', 'X', 'X'),
                ('Y', 'Y', 'Y')]
    bpy.types.Object.Dimension_XYType = bpy.props.EnumProperty(name = "XY",
                description = "XY",
                items = XYTypes)
    XZTypes = [
                ('X', 'X', 'X'),
                ('Z', 'Z', 'Z')]
    bpy.types.Object.Dimension_XZType = bpy.props.EnumProperty(name = "XZ",
                description = "XZ",
                items = XZTypes)
    YZTypes = [
                ('Y', 'Y', 'Y'),
                ('Z', 'Z', 'Z')]
    bpy.types.Object.Dimension_YZType = bpy.props.EnumProperty(name = "YZ",
                description = "YZ",
                items = YZTypes)
    bpy.types.Object.Dimension_YZType = bpy.props.EnumProperty(name = "Coordinate system",
                description = "Place in a coordinate system",
                items = YZTypes)
    bpy.types.Object.Dimension_startlocation = bpy.props.FloatVectorProperty(name = "Start location",
                description = "",
                subtype = 'XYZ',
                update = StartLocationUpdate)
    bpy.types.Object.Dimension_endlocation = bpy.props.FloatVectorProperty(name = "End location",
                description = "",
                subtype = 'XYZ')
    bpy.types.Object.Dimension_endanglelocation = bpy.props.FloatVectorProperty(name = "End angle location",
                description = "End angle location",
                subtype = 'XYZ')
    width_or_location_items = [
                ('width', 'width', 'width'),
                ('location', 'location', 'location')]
    bpy.types.Object.Dimension_width_or_location = bpy.props.EnumProperty(name = "width or location",
                items = width_or_location_items,
                description = "width or location")
    libertyItems = [
                ('2D', '2D', '2D'),
                ('3D', '3D', '3D')]
    bpy.types.Object.Dimension_liberty = bpy.props.EnumProperty(name = "2D / 3D",
                items = libertyItems,
                description = "2D or 3D Dimension")

    ### Arrow
    Arrows = [
                ('Arrow1', 'Arrow1', 'Arrow1'),
                ('Arrow2', 'Arrow2', 'Arrow2'),
                ('Serifs1', 'Serifs1', 'Serifs1'),
                ('Serifs2', 'Serifs2', 'Serifs2'),
                ('Without', 'Without', 'Without')]
    bpy.types.Object.Dimension_arrow = bpy.props.EnumProperty(name = "Arrow",
                items = Arrows,
                description = "Arrow")
    bpy.types.Object.Dimension_arrowdepth = bpy.props.FloatProperty(name = "Depth",
                    min = 0, soft_min = 0,
                    description = "Arrow depth")
    bpy.types.Object.Dimension_arrowlength = bpy.props.FloatProperty(name = "Length",
                    min = 0, soft_min = 0,
                    description = "Arrow length")

    #### Dimension properties
    bpy.types.Object.Dimension_resolution = bpy.props.IntProperty(name = "Resolution",
                    min = 1, soft_min = 1,
                    description = "Resolution")
    bpy.types.Object.Dimension_width = bpy.props.FloatProperty(name = "Width",
                    unit = 'LENGTH',
                    description = "Width")
    bpy.types.Object.Dimension_length = bpy.props.FloatProperty(name = "Length",
                    description = "Length")
    bpy.types.Object.Dimension_dsize = bpy.props.FloatProperty(name = "Size",
                    min = 0, soft_min = 0,
                    description = "Size")
    bpy.types.Object.Dimension_depth = bpy.props.FloatProperty(name = "Depth",
                    min = 0, soft_min = 0,
                    description = "Depth")
    bpy.types.Object.Dimension_depth_from_center = bpy.props.BoolProperty(name = "Depth from center",
                    description = "Depth from center")
    bpy.types.Object.Dimension_angle = bpy.props.FloatProperty(name = "Angle",
                    description = "Angle")
    bpy.types.Object.Dimension_rotation = bpy.props.FloatProperty(name = "Rotation",
                    description = "Rotation")

    #### Dimension units properties
    Units = [
                ('None', 'None', 'None'),
                ('\u00b5m', '\u00b5m', '\u00b5m'),
                ('mm', 'mm', 'mm'),
                ('cm', 'cm', 'cm'),
                ('m', 'm', 'm'),
                ('km', 'km', 'km'),
                ('thou', 'thou', 'thou'),
                ('"', '"', '"'),
                ('\'', '\'', '\''),
                ('yd', 'yd', 'yd'),
                ('mi', 'mi', 'mi')]
    bpy.types.Object.Dimension_units = bpy.props.EnumProperty(name = "Units",
                items = Units,
                description = "Units")
    bpy.types.Object.Dimension_add_units_name = bpy.props.BoolProperty(name = "Add units name",
                description = "Add units name")
    bpy.types.Object.Dimension_offset = bpy.props.FloatProperty(name = "Offset",
                description = "Offset")

    #### Dimension text properties
    bpy.types.Object.Dimension_textsize = bpy.props.FloatProperty(name = "Size",
                    description = "Size")
    bpy.types.Object.Dimension_textdepth = bpy.props.FloatProperty(name = "Depth",
                    description = "Depth")
    bpy.types.Object.Dimension_textround = bpy.props.IntProperty(name = "Rounding",
                    min = 0, soft_min = 0,
                    description = "Rounding")
    bpy.types.Object.Dimension_font = bpy.props.StringProperty(name = "Font",
                    subtype = 'FILE_PATH',
                    description = "Font")

    #### Materials properties
    bpy.types.Object.Dimension_matname = bpy.props.StringProperty(name = "Name",
                    default = 'Dimension_Red',
                    description = "Material name")

    #### Note text
    bpy.types.Object.Dimension_note = bpy.props.StringProperty(name = "Note",
                    default = 'Note',
                    description = "Note text")
    bpy.types.Object.Dimension_align_to_camera = bpy.props.BoolProperty(name = "Align to camera",
                description = "Align to camera")

    #### Parent
    bpy.types.Object.Dimension_parent = bpy.props.StringProperty(name = "Parent",
                    default = '',
                    description = "Parent")
    bpy.types.Object.Dimension_appoint_parent = bpy.props.BoolProperty(name = "Appoint parent",
                description = "Appoint parent")

################################################################################
##### REGISTER #####

def Dimension_button(self, context):
    oper = self.layout.operator(Dimension.bl_idname, text = "Dimension", icon = "PLUGIN")
    oper.Dimension_Change = False
    oper.Dimension_width_or_location = 'width'
    oper.Dimension_liberty = '2D'

def register():
    bpy.utils.register_module(__name__)

    bpy.types.VIEW3D_MT_curve_add.append(Dimension_button)

    DimensionVariables()

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.VIEW3D_MT_curve_add.remove(Dimension_button)

if __name__ == "__main__":
    register()
