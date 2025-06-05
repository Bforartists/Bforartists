# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import blf
import bpy_extras
import numpy as np
import gpu
from gpu_extras.batch import batch_for_shader
from math import(
    cos,
    sin,
    ceil,
    floor,
    )

from bpy_extras.view3d_utils import (
    region_2d_to_location_3d,
    location_3d_to_region_2d,
)

from .carver_utils import (
    draw_circle,
    draw_shader,
    objDiagonal,
    mini_grid,
    )

from mathutils import (
    Color,
    Euler,
    Vector,
    Quaternion,
)

def get_text_info(self, context, help_txt):
    """ Return the dimensions of each part of the text """

    #Extract the longest first option in sublist
    max_option = max(list(blf.dimensions(0, row[0])[0] for row in help_txt))

    #Extract the longest key in sublist
    max_key = max(list(blf.dimensions(0, row[1])[0] for row in help_txt))

    #Space between option and key  with a comma separator (" : ")
    comma = blf.dimensions(0, "_:_")[0]

    #Get a default height for all the letters
    line_height = (blf.dimensions(0, "gM")[1] * 1.45)

    #Get the total height of the text
    bloc_height = 0
    for row in help_txt:
        bloc_height += line_height

    return(help_txt, bloc_height, max_option, max_key, comma)

def draw_string(self, color1, color2, left, bottom, text, max_option, divide = 1):
    """ Draw the text like 'option : key' or just 'option' """

    font_id = 0
    ui_scale = bpy.context.preferences.system.ui_scale

    blf.enable(font_id,blf.SHADOW)
    blf.shadow(font_id, 0, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font_id,2,-2)
    line_height = (blf.dimensions(font_id, "gM")[1] * 1.45)
    y_offset = 5

    # Test if the text is a list formatted like : ('option', 'key')
    if isinstance(text,list):
        spacer_text = " : "
        spacer_width = blf.dimensions(font_id, spacer_text)[0]
        for string in text:
            blf.position(font_id, (left), (bottom + y_offset), 0)
            blf.color(font_id, *color1)
            blf.draw(font_id, string[0])
            blf.position(font_id, (left + max_option), (bottom + y_offset), 0)
            blf.draw(font_id, spacer_text)
            blf.color(font_id, *color2)
            blf.position(font_id, (left + max_option + spacer_width), (bottom + y_offset), 0)
            blf.draw(font_id, string[1])
            y_offset += line_height
    else:
        # The text is formatted like : ('option')
        blf.position(font_id, left, (bottom + y_offset), 0)
        blf.color(font_id, *color1)
        blf.draw(font_id, text)
        y_offset += line_height

    blf.disable(font_id,blf.SHADOW)

# Opengl draw on screen
def draw_callback_px(self, context):
    font_id = 0
    region = context.region
    UIColor = (0.992, 0.5518, 0.0, 1.0)

    # Cut Type
    RECTANGLE = 0
    LINE = 1
    CIRCLE = 2
    self.carver_prefs = context.preferences.addons[__package__].preferences

    # Color
    color1 = (1.0, 1.0, 1.0, 1.0)
    color2 = UIColor

    #The mouse is outside the active region
    if not self.in_view_3d:
        color1 = color2 = (1.0, 0.2, 0.1, 1.0)

    # Primitives type
    PrimitiveType = "Rectangle"
    if self.CutType == CIRCLE:
        PrimitiveType = "Circle"
    if self.CutType == LINE:
        PrimitiveType = "Line"

    # Width screen
    overlap = context.preferences.system.use_region_overlap

    t_panel_width = 0
    if overlap:
        for region in context.area.regions:
            if region.type == 'TOOLS':
                t_panel_width = region.width

    # Initial position
    region_width = int(region.width / 2.0)
    y_txt = 10


    # Draw the center command from bottom to top

    # Get the size of the text
    text_size = 18 if region.width >= 850 else 12
    ui_scale = bpy.context.preferences.system.ui_scale
    blf.size(0, round(text_size * ui_scale))

    # Help Display
    if (self.ObjectMode is False) and (self.ProfileMode is False):

        # Depth Cursor
        TypeStr = "Cursor Depth [" + self.carver_prefs.Key_Depth + "]"
        BoolStr = "(ON)" if self.snapCursor else "(OFF)"
        help_txt = [[TypeStr, BoolStr]]

        # Close poygonal shape
        if self.CreateMode and self.CutType == LINE:
            TypeStr = "Close [" + self.carver_prefs.Key_Close + "]"
            BoolStr = "(ON)" if self.Closed else "(OFF)"
            help_txt += [[TypeStr, BoolStr]]

        if self.CreateMode is False:
            # Apply Booleans
            TypeStr = "Apply Operations [" + self.carver_prefs.Key_Apply + "]"
            BoolStr = "(OFF)" if self.dont_apply_boolean else "(ON)"
            help_txt += [[TypeStr, BoolStr]]

            #Auto update for bevel
            TypeStr = "Bevel Update [" + self.carver_prefs.Key_Update + "]"
            BoolStr = "(ON)" if self.Auto_BevelUpdate else "(OFF)"
            help_txt += [[TypeStr, BoolStr]]

        # Circle subdivisions
        if self.CutType == CIRCLE:
            TypeStr = "Subdivisions [" + self.carver_prefs.Key_Subrem + "][" + self.carver_prefs.Key_Subadd + "]"
            BoolStr = str((int(360 / self.stepAngle[self.step])))
            help_txt += [[TypeStr, BoolStr]]

        if self.CreateMode:
            help_txt += [["Type [Space]", PrimitiveType]]
        else:
            help_txt += [["Cut Type [Space]", PrimitiveType]]

    else:
        # Instantiate
        TypeStr = "Instantiate [" + self.carver_prefs.Key_Instant + "]"
        BoolStr = "(ON)" if self.Instantiate else "(OFF)"
        help_txt = [[TypeStr, BoolStr]]

        # Random rotation
        if self.alt:
            TypeStr = "Random Rotation [" + self.carver_prefs.Key_Randrot + "]"
            BoolStr = "(ON)" if self.RandomRotation else "(OFF)"
            help_txt += [[TypeStr, BoolStr]]

        # Thickness
        if self.BrushSolidify:
            TypeStr = "Thickness [" + self.carver_prefs.Key_Depth + "]"
            if self.ProfileMode:
                BoolStr = str(round(self.ProfileBrush.modifiers["CT_SOLIDIFY"].thickness, 2))
            if self.ObjectMode:
                BoolStr = str(round(self.ObjectBrush.modifiers["CT_SOLIDIFY"].thickness, 2))
            help_txt += [[TypeStr, BoolStr]]

        # Brush depth
        if (self.ObjectMode):
            TypeStr = "Carve Depth [" + self.carver_prefs.Key_Depth + "]"
            BoolStr = str(round(self.ObjectBrush.data.vertices[0].co.z, 2))
            help_txt += [[TypeStr, BoolStr]]

            TypeStr = "Brush Depth [" + self.carver_prefs.Key_BrushDepth + "]"
            BoolStr = str(round(self.BrushDepthOffset, 2))
            help_txt += [[TypeStr, BoolStr]]

    help_txt, bloc_height, max_option, max_key, comma = get_text_info(self, context, help_txt)
    xCmd = region_width - (max_option + max_key + comma) / 2
    draw_string(self, color1, color2, xCmd, y_txt, help_txt, max_option, divide = 2)


    # Separator (Line)
    LineWidth = (max_option + max_key + comma) / 2
    if region.width >= 850:
        LineWidth = 140

    LineWidth = (max_option + max_key + comma)
    coords = [(int(region_width - LineWidth/2), y_txt + bloc_height + 8), \
              (int(region_width + LineWidth/2), y_txt + bloc_height + 8)]
    draw_shader(self, UIColor, 1, 'LINES', coords, self.carver_prefs.LineWidth)

    # Command Display
    if self.CreateMode and ((self.ObjectMode is False) and (self.ProfileMode is False)):
        BooleanMode = "Create"
    else:
        if self.ObjectMode or self.ProfileMode:
            BooleanType = "Difference) [T]" if self.BoolOps == self.difference else "Union) [T]"
            BooleanMode = \
                "Object Brush (" + BooleanType if self.ObjectMode else "Profil Brush (" + BooleanType
        else:
            BooleanMode = \
                "Difference" if (self.shift is False) and (self.ForceRebool is False) else "Rebool"

    # Display boolean mode
    text_size = 40 if region.width >= 850 else 20
    blf.size(0, round(text_size * ui_scale))

    draw_string(self, color2, color2, region_width - (blf.dimensions(0, BooleanMode)[0]) / 2, \
                y_txt + bloc_height + 16, BooleanMode, 0, divide = 2)

    if region.width >= 850:

        if self.AskHelp is False:
            # "H for Help" text
            blf.size(0, round(13 * ui_scale))
            help_txt = "[" + self.carver_prefs.Key_Help + "] for help"
            txt_width = blf.dimensions(0, help_txt)[0]
            txt_height = (blf.dimensions(0, "gM")[1] * 1.45)

            # Draw a rectangle and put the text "H for Help"
            xrect = 40
            yrect = 40
            rect_vertices = [(xrect - 5, yrect - 5), (xrect + txt_width + 5, yrect - 5), \
                             (xrect + txt_width + 5, yrect + txt_height + 5), (xrect - 5, yrect + txt_height + 5)]
            draw_shader(self, (0.0, 0.0, 0.0),  0.3, 'TRI_FAN', rect_vertices, self.carver_prefs.LineWidth)
            draw_string(self, color1, color2, xrect, yrect, help_txt, 0)

        else:
            #Draw the help text
            xHelp = 30 + t_panel_width
            yHelp = 10

            if self.ObjectMode or self.ProfileMode:
                if self.ProfileMode:
                    help_txt = [["Object Mode", self.carver_prefs.Key_Brush]]
                else:
                    help_txt = [["Cut Mode", self.carver_prefs.Key_Brush]]

            else:
                help_txt =[
                      ["Profil Brush", self.carver_prefs.Key_Brush],\
                      ["Move Cursor", "Ctrl + LMB"]
                      ]

            if (self.ObjectMode is False) and (self.ProfileMode is False):
                if self.CreateMode is False:
                    help_txt +=[
                           ["Create geometry", self.carver_prefs.Key_Create],\
                           ]
                else:
                    help_txt +=[
                           ["Cut", self.carver_prefs.Key_Create],\
                           ]
                if self.CutMode == RECTANGLE:
                    help_txt +=[
                           ["Dimension", "MouseMove"],\
                           ["Move all", "Alt"],\
                           ["Validate", "LMB"],\
                           ["Rebool", "Shift"]
                           ]

                elif self.CutMode == CIRCLE:
                    help_txt +=[
                           ["Rotation and Radius", "MouseMove"],\
                           ["Move all", "Alt"],\
                           ["Subdivision", self.carver_prefs.Key_Subrem + " " + self.carver_prefs.Key_Subadd],\
                           ["Incremental rotation", "Ctrl"],\
                           ["Rebool", "Shift"]
                           ]

                elif self.CutMode == LINE:
                    help_txt +=[
                           ["Dimension", "MouseMove"],\
                           ["Move all", "Alt"],\
                           ["Validate", "Space"],\
                           ["Rebool", "Shift"],\
                           ["Snap", "Ctrl"],\
                           ["Scale Snap", "WheelMouse"],\
                           ]
            else:
                # ObjectMode
                help_txt +=[
                       ["Difference", "Space"],\
                       ["Rebool", "Shift + Space"],\
                       ["Duplicate", "Alt + Space"],\
                       ["Scale", self.carver_prefs.Key_Scale],\
                       ["Rotation", "LMB + Move"],\
                       ["Step Angle", "CTRL + LMB + Move"],\
                       ]

                if self.ProfileMode:
                    help_txt +=[["Previous or Next Profile", self.carver_prefs.Key_Subadd + " " + self.carver_prefs.Key_Subrem]]

                help_txt +=[
                       ["Create / Delete rows",  chr(8597)],\
                       ["Create / Delete cols",  chr(8596)],\
                       ["Gap for rows or columns",  self.carver_prefs.Key_Gapy + " " + self.carver_prefs.Key_Gapx]
                       ]

            blf.size(0, round(15 * ui_scale))
            help_txt, bloc_height, max_option, max_key, comma = get_text_info(self, context, help_txt)
            draw_string(self, color1, color2, xHelp, yHelp, help_txt, max_option)

    if self.ProfileMode:
        xrect = region.width - t_panel_width - 80
        yrect = 80
        coords = [(xrect, yrect), (xrect+60, yrect), (xrect+60, yrect-60), (xrect, yrect-60)]

        # Draw rectangle background in the lower right
        draw_shader(self, (0.0, 0.0, 0.0),  0.3, 'TRI_FAN', coords, size=self.carver_prefs.LineWidth)

        # Use numpy to get the vertices and indices of the profile object to draw
        WidthProfil = 50
        location = Vector((region.width - t_panel_width - WidthProfil, 50, 0))
        ProfilScale = 20.0
        coords = []
        mesh = bpy.data.meshes[self.Profils[self.nProfil][0]]
        mesh.calc_loop_triangles()
        vertices = np.empty((len(mesh.vertices), 3), 'f')
        indices = np.empty((len(mesh.loop_triangles), 3), 'i')
        mesh.vertices.foreach_get("co", np.reshape(vertices, len(mesh.vertices) * 3))
        mesh.loop_triangles.foreach_get("vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))

        for idx, vals in enumerate(vertices):
            coords.append([
            vals[0] * ProfilScale + location.x,
            vals[1] * ProfilScale + location.y,
            vals[2] * ProfilScale + location.z
            ])

        #Draw the silhouette of the mesh
        draw_shader(self, UIColor,  0.5, 'TRIS', coords, size=self.carver_prefs.LineWidth, indices=indices)


    if self.CutMode:

        if len(self.mouse_path) > 1:
            x0 = self.mouse_path[0][0]
            y0 = self.mouse_path[0][1]
            x1 = self.mouse_path[1][0]
            y1 = self.mouse_path[1][1]

        # Cut rectangle
        if self.CutType == RECTANGLE:
            coords = [
            (x0 + self.xpos, y0 + self.ypos), (x1 + self.xpos, y0 + self.ypos), \
            (x1 + self.xpos, y1 + self.ypos), (x0 + self.xpos, y1 + self.ypos)
            ]
            indices = ((0, 1, 2), (2, 0, 3))

            self.rectangle_coord = coords

            draw_shader(self, UIColor, 1, 'LINE_LOOP', coords, size=self.carver_prefs.LineWidth)

            #Draw points
            draw_shader(self, UIColor, 1, 'POINTS', coords, size=3)

            if self.shift or self.CreateMode:
                draw_shader(self, UIColor, 0.5, 'TRIS', coords, size=self.carver_prefs.LineWidth, indices=indices)

            # Draw grid (based on the overlay options) to show the incremental snapping
            if self.ctrl:
                mini_grid(self, context, UIColor)

        # Cut Line
        elif self.CutType == LINE:
            coords = []
            indices = []
            top_grid = False

            for idx, vals in enumerate(self.mouse_path):
                coords.append([vals[0] + self.xpos, vals[1] + self.ypos])
                indices.append([idx])

            # Draw lines
            if self.Closed:
                draw_shader(self, UIColor, 1.0, 'LINE_LOOP', coords, size=self.carver_prefs.LineWidth)
            else:
                draw_shader(self, UIColor, 1.0, 'LINE_STRIP', coords, size=self.carver_prefs.LineWidth)

            # Draw points
            draw_shader(self, UIColor, 1.0, 'POINTS', coords, size=3)

            # Draw polygon
            if (self.shift) or (self.CreateMode and self.Closed):
                draw_shader(self, UIColor, 0.5, 'TRI_FAN', coords, size=self.carver_prefs.LineWidth)

            # Draw grid (based on the overlay options) to show the incremental snapping
            if self.ctrl:
                mini_grid(self, context, UIColor)

        # Circle Cut
        elif self.CutType == CIRCLE:
            # Create a circle using a tri fan
            tris_coords, indices = draw_circle(self, x0, y0)

            # Remove the vertex in the center to get the outer line of the circle
            line_coords = tris_coords[1:]
            draw_shader(self, UIColor, 1.0, 'LINE_LOOP', line_coords, size=self.carver_prefs.LineWidth)

            if self.shift or self.CreateMode:
                draw_shader(self, UIColor, 0.5, 'TRIS', tris_coords, size=self.carver_prefs.LineWidth, indices=indices)

    if (self.ObjectMode or self.ProfileMode) and len(self.CurrentSelection) > 0:
        if self.ShowCursor:
            region = context.region
            rv3d = context.space_data.region_3d

            if self.ObjectMode:
                ob = self.ObjectBrush
            if self.ProfileMode:
                ob = self.ProfileBrush
            mat = ob.matrix_world

            # 50% alpha, 2 pixel width line
            gpu.state.blend_set('ALPHA')

            bbox = [mat @ Vector(b) for b in ob.bound_box]
            objBBDiagonal = objDiagonal(self.CurrentSelection[0])

            if self.shift:
                gl_size = 4
                UIColor = (0.5, 1.0, 0.0, 1.0)
            else:
                gl_size = 2
                UIColor = (1.0, 0.8, 0.0, 1.0)

            line_coords = []
            idx = 0
            CRadius = ((bbox[7] - bbox[0]).length) / 2
            for i in range(int(len(self.CLR_C) / 3)):
                vector3d = (self.CLR_C[idx * 3] * CRadius + self.CurLoc.x, \
                            self.CLR_C[idx * 3 + 1] * CRadius + self.CurLoc.y, \
                            self.CLR_C[idx * 3 + 2] * CRadius + self.CurLoc.z)
                vector2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, vector3d)
                if vector2d is not None:
                    line_coords.append((vector2d[0], vector2d[1]))
                idx += 1
            if len(line_coords) > 0 :
                draw_shader(self, UIColor, 1.0, 'LINE_LOOP', line_coords, size=gl_size)

            # Object display
            if self.quat_rot is not None:
                ob.location = self.CurLoc
                v = Vector()
                v.x = v.y = 0.0
                v.z = self.BrushDepthOffset
                ob.location += self.quat_rot @ v

                e = Euler()
                e.x = 0.0
                e.y = 0.0
                e.z = self.aRotZ / 25.0

                qe = e.to_quaternion()
                qRot = self.quat_rot @ qe
                ob.rotation_mode = 'QUATERNION'
                ob.rotation_quaternion = qRot
                ob.rotation_mode = 'XYZ'

                if self.ProfileMode:
                    if self.ProfileBrush is not None:
                        self.ProfileBrush.location = self.CurLoc
                        self.ProfileBrush.rotation_mode = 'QUATERNION'
                        self.ProfileBrush.rotation_quaternion = qRot
                        self.ProfileBrush.rotation_mode = 'XYZ'

    # Opengl defaults
    gpu.state.blend_set('NONE')
