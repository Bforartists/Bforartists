# SPDX-FileCopyrightText: 2020-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

'''Based on GP_refine_stroke 0.2.4 - Author: Samuel Bernou'''

import bpy

### --- Vector utils

def mean(*args):
    '''
    return mean of all passed value (multiple)
    If it's a list or tuple return mean of it (only on first list passed).
    '''
    if isinstance(args[0], list) or isinstance(args[0], tuple):
        return mean(*args[0])#send the first list UNPACKED (else infinite recursion as it always evaluate as list)
    return sum(args) / len(args)

def vector_len_from_coord(a, b):
    '''
    Get two points (that has coordinate 'co' attribute) or Vectors (2D or 3D)
    Return length as float
    '''
    from mathutils import Vector
    if type(a) is Vector:
        return (a - b).length
    else:
        return (a.co - b.co).length

def point_from_dist_in_segment_3d(a, b, ratio):
    '''return the tuple coords of a point on 3D segment ab according to given ratio (some distance divided by total segment length)'''
    ## ref:https://math.stackexchange.com/questions/175896/finding-a-point-along-a-line-a-certain-distance-away-from-another-point
    # ratio = dist / seglength
    return ( ((1 - ratio) * a[0] + (ratio*b[0])), ((1 - ratio) * a[1] + (ratio*b[1])), ((1 - ratio) * a[2] + (ratio*b[2])) )

def get_stroke_length(s):
    '''return 3D total length of the stroke'''
    all_len = 0.0
    for i in range(0, len(s.points)-1):
        #print(vector_len_from_coord(s.points[i],s.points[i+1]))
        all_len += vector_len_from_coord(s.points[i],s.points[i+1])
    return (all_len)

### --- Functions

def to_straight_line(s, keep_points=True, influence=100, straight_pressure=True):
    '''
    keep points : if false only start and end point stay
    straight_pressure : (not available with keep point) take the mean pressure of all points and apply to stroke.
    '''

    p_len = len(s.points)
    if p_len <= 2: # 1 or 2 points only, cancel
        return

    if not keep_points:
        if straight_pressure: mean_pressure = mean([p.pressure for p in s.points])#can use a foreach_get but might not be faster.
        for i in range(p_len-2):
            s.points.pop(index=1)
        if straight_pressure:
            for p in s.points:
                p.pressure = mean_pressure

    else:
        A = s.points[0].co
        B = s.points[-1].co
        # ab_dist = vector_len_from_coord(A,B)
        full_dist = get_stroke_length(s)
        dist_from_start = 0.0
        coord_list = []

        for i in range(1, p_len-1):#all but first and last
            dist_from_start += vector_len_from_coord(s.points[i-1],s.points[i])
            ratio = dist_from_start / full_dist
            # dont apply directly (change line as we measure it in loop)
            coord_list.append( point_from_dist_in_segment_3d(A, B, ratio) )

        # apply change
        for i in range(1, p_len-1):
            ## Direct super straight 100%
            #s.points[i].co = coord_list[i-1]

            ## With influence
            s.points[i].co = point_from_dist_in_segment_3d(s.points[i].co, coord_list[i-1], influence / 100)

    return

def get_last_index(context=None):
    if not context:
        context = bpy.context
    return 0 if context.tool_settings.use_gpencil_draw_onback else -1

### --- OPS

class GP_OT_straightStroke(bpy.types.Operator):
    bl_idname = "gp.straight_stroke"
    bl_label = "Straight Stroke"
    bl_description = "Make stroke a straight line between first and last point, tweak influence in the redo panel\
        \nshift+click to reset infuence to 100%"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.object.type == 'GPENCIL'
        #and context.mode in ('PAINT_GPENCIL', 'EDIT_GPENCIL')

    influence_val : bpy.props.FloatProperty(name="Straight force", description="Straight interpolation percentage",
    default=100, min=0, max=100, step=2, precision=1, subtype='PERCENTAGE', unit='NONE')

    def execute(self, context):
        gp = context.object.data
        gpl = gp.layers
        if not gpl:
            return {"CANCELLED"}

        if context.mode == 'PAINT_GPENCIL':
            if not gpl.active or not gpl.active.active_frame:
                self.report({'ERROR'}, 'No Grease pencil frame found')
                return {"CANCELLED"}

            if not len(gpl.active.active_frame.strokes):
                self.report({'ERROR'}, 'No strokes found.')
                return {"CANCELLED"}

            s = gpl.active.active_frame.strokes[get_last_index(context)]
            to_straight_line(s, keep_points=True, influence=self.influence_val)

        elif context.mode == 'EDIT_GPENCIL':
            ct = 0
            for l in gpl:
                if l.lock or l.hide or not l.active_frame:
                    # avoid locked, hidden, empty layers
                    continue
                if gp.use_multiedit:
                    target_frames = [f for f in l.frames if f.select]
                else:
                    target_frames = [l.active_frame]

                for f in target_frames:
                    for s in f.strokes:
                        if s.select:
                            ct += 1
                            to_straight_line(s, keep_points=True, influence=self.influence_val)

            if not ct:
                self.report({'ERROR'}, 'No selected stroke found.')
                return {"CANCELLED"}

        ## filter method
        # if context.mode == 'PAINT_GPENCIL':
        #     L, F, S = 'ACTIVE', 'ACTIVE', 'LAST'
        # elif context.mode == 'EDIT_GPENCIL'
        #     L, F, S = 'ALL', 'ACTIVE', 'SELECT'
        #     if gp.use_multiedit: F = 'SELECT'
        # else : return {"CANCELLED"}
        # for s in strokelist(t_layer=L, t_frame=F, t_stroke=S):
        #     to_straight_line(s, keep_points=True, influence = self.influence_val)#, straight_pressure=True

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "influence_val")

    def invoke(self, context, event):
        if context.mode not in ('PAINT_GPENCIL', 'EDIT_GPENCIL'):
            return {"CANCELLED"}
        if event.shift:
            self.influence_val = 100
        return self.execute(context)


def register():
    bpy.utils.register_class(GP_OT_straightStroke)

def unregister():
    bpy.utils.unregister_class(GP_OT_straightStroke)
