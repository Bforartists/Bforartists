# SPDX-FileCopyrightText: 2020-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

'''Based on Box_deform standalone addon - Author: Samuel Bernou'''

from .prefs import get_addon_prefs

import bpy
import numpy as np

def location_to_region(worldcoords):
    from bpy_extras import view3d_utils
    return view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords):
    from bpy_extras import view3d_utils
    return view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, viewcoords, depthcoords)

def store_cage(self, vg_name):
    import time
    unique_id = time.strftime(r'%y%m%d%H%M%S') # ex: 20210711111117
    # name = f'gp_lattice_{unique_id}'
    name = f'{self.gp_obj.name}_lat{unique_id}'
    vg = self.gp_obj.vertex_groups.get(vg_name)
    if vg:
        vg.name = name
    for o in self.other_gp:
        vg = o.vertex_groups.get(vg_name)
        if vg:
            vg.name = name

    self.cage.name = name
    self.cage.data.name = name
    mod = self.gp_obj.grease_pencil_modifiers.get('tmp_lattice')
    if mod:
        mod.name = name #f'Lattice_{unique_id}'
        mod.vertex_group = name
    for o in self.other_gp:
        mod = o.grease_pencil_modifiers.get('tmp_lattice')
        if mod:
            mod.name = name
            mod.vertex_group = name

def assign_vg(obj, vg_name, delete=False):
    ## create vertex group
    vg = obj.vertex_groups.get(vg_name)
    if vg:
        # remove to start clean
        obj.vertex_groups.remove(vg)
    if delete:
        return

    vg = obj.vertex_groups.new(name=vg_name)
    bpy.ops.gpencil.vertex_group_assign()
    return vg

def view_cage(obj):
    prefs = get_addon_prefs()
    lattice_interp = prefs.default_deform_type

    gp = obj.data
    gpl = gp.layers

    from_obj = bpy.context.mode == 'OBJECT'
    all_gps = [o for o in bpy.context.selected_objects if o.type == 'GPENCIL']
    other_gp = [o for o in all_gps if o is not obj]

    coords = []
    initial_mode = bpy.context.mode

    ## get points
    if bpy.context.mode == 'EDIT_GPENCIL':
        for l in gpl:
            if l.lock or l.hide or not l.active_frame:#or len(l.frames)
                continue
            if gp.use_multiedit:
                target_frames = [f for f in l.frames if f.select]
            else:
                target_frames = [l.active_frame]

            for f in target_frames:
                for s in f.strokes:
                    if not s.select:
                        continue
                    for p in s.points:
                        if p.select:
                            # get real location
                            coords.append(obj.matrix_world @ p.co)

    elif bpy.context.mode == 'OBJECT': # object mode -> all points of all selected gp objects
        for gpo in all_gps:
            for l in gpo.data.layers:# if l.hide:continue# only visible ? (might break things)
                if not len(l.frames):
                    continue # skip frameless layer
                for s in l.active_frame.strokes:
                    for p in s.points:
                        coords.append(gpo.matrix_world @ p.co)

    elif bpy.context.mode == 'PAINT_GPENCIL':
        # get last stroke points coordinated
        if not gpl.active or not gpl.active.active_frame:
            return 'No frame to deform'

        if not len(gpl.active.active_frame.strokes):
            return 'No stroke found to deform'

        paint_id = -1
        if bpy.context.scene.tool_settings.use_gpencil_draw_onback:
            paint_id = 0
        coords = [obj.matrix_world @ p.co for p in gpl.active.active_frame.strokes[paint_id].points]

    else:
        return 'Wrong mode!'

    if not coords:
        ## maybe silent return instead (need special str code to manage errorless return)
        return 'No points found!'

    if bpy.context.mode in ('EDIT_GPENCIL', 'PAINT_GPENCIL') and len(coords) < 2:
        # Dont block object mod
        return 'Less than two point selected'

    vg_name = 'lattice_cage_deform_group'

    if bpy.context.mode == 'EDIT_GPENCIL':
        vg = assign_vg(obj, vg_name)

    if bpy.context.mode == 'PAINT_GPENCIL':
        # points cannot be assign to API yet(ugly and slow workaround but only way)
        # -> https://developer.blender.org/T56280 so, hop'in'ops !

        # store selection and deselect all
        plist = []
        for s in gpl.active.active_frame.strokes:
            for p in s.points:
                plist.append([p, p.select])
                p.select = False

        # select
        ## foreach_set does not update
        # gpl.active.active_frame.strokes[paint_id].points.foreach_set('select', [True]*len(gpl.active.active_frame.strokes[paint_id].points))
        for p in gpl.active.active_frame.strokes[paint_id].points:
            p.select = True

        # assign
        bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
        vg = assign_vg(obj, vg_name)

        # restore
        for pl in plist:
            pl[0].select = pl[1]


    ## View axis Mode ---

    ## get view coordinate of all points
    coords2D = [location_to_region(co) for co in coords]

    # find centroid for depth (or more economic, use obj origin...)
    centroid = np.mean(coords, axis=0)

    # not a mean ! a mean of extreme ! centroid2d = np.mean(coords2D, axis=0)
    all_x, all_y = np.array(coords2D)[:, 0], np.array(coords2D)[:, 1]
    min_x, min_y = np.min(all_x), np.min(all_y)
    max_x, max_y = np.max(all_x), np.max(all_y)

    width = (max_x - min_x)
    height = (max_y - min_y)
    center_x = min_x + (width/2)
    center_y = min_y + (height/2)

    centroid2d = (center_x,center_y)
    center = region_to_location(centroid2d, centroid)
    # bpy.context.scene.cursor.location = center#Dbg


    #corner Bottom-left to Bottom-right
    x0 = region_to_location((min_x, min_y), centroid)
    x1 = region_to_location((max_x, min_y), centroid)
    x_worldsize = (x0 - x1).length

    #corner Bottom-left to top-left
    y0 = region_to_location((min_x, min_y), centroid)
    y1 = region_to_location((min_x, max_y), centroid)
    y_worldsize = (y0 - y1).length

    ## in case of 3

    lattice_name = 'lattice_cage_deform'
    # cleaning
    cage = bpy.data.objects.get(lattice_name)
    if cage:
        bpy.data.objects.remove(cage)

    lattice = bpy.data.lattices.get(lattice_name)
    if lattice:
        bpy.data.lattices.remove(lattice)

    # create lattice object
    lattice = bpy.data.lattices.new(lattice_name)
    cage = bpy.data.objects.new(lattice_name, lattice)
    cage.show_in_front = True

    ## Master (root) collection
    bpy.context.scene.collection.objects.link(cage)

    # spawn cage and align it to view

    r3d = bpy.context.space_data.region_3d
    viewmat = r3d.view_matrix

    cage.matrix_world = viewmat.inverted()
    cage.scale = (x_worldsize, y_worldsize, 1)
    ## Z aligned in view direction (need minus X 90 degree to be aligned FRONT)
    # cage.rotation_euler.x -= radians(90)
    # cage.scale = (x_worldsize, 1, y_worldsize)
    cage.location = center

    lattice.points_u = 2
    lattice.points_v = 2
    lattice.points_w = 1

    lattice.interpolation_type_u = lattice_interp #'KEY_LINEAR'-'KEY_BSPLINE'
    lattice.interpolation_type_v = lattice_interp
    lattice.interpolation_type_w = lattice_interp

    mod = obj.grease_pencil_modifiers.new('tmp_lattice', 'GP_LATTICE')
    if from_obj:
        mods = []
        for o in other_gp:
            mods.append( o.grease_pencil_modifiers.new('tmp_lattice', 'GP_LATTICE') )

    # move to top if modifiers exists
    for _ in range(len(obj.grease_pencil_modifiers)):
        bpy.ops.object.gpencil_modifier_move_up(modifier='tmp_lattice')
    if from_obj:
        for o in other_gp:
            for _ in range(len(o.grease_pencil_modifiers)):
                context_override = {'object': o}
                with bpy.context.temp_override(**context_override):
                    bpy.ops.object.gpencil_modifier_move_up(modifier='tmp_lattice')

    mod.object = cage
    if from_obj:
        for m in mods:
            m.object = cage

    if initial_mode == 'PAINT_GPENCIL':
        mod.layer = gpl.active.info

    # note : if initial was Paint, changed to Edit
    #        so vertex attribution is valid even for paint
    if bpy.context.mode == 'EDIT_GPENCIL':
        mod.vertex_group = vg.name

    # Go in object mode if not already
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Store name of deformed object in case of 'revive modal'
    cage.vertex_groups.new(name=obj.name)
    if from_obj:
        for o in other_gp:
            cage.vertex_groups.new(name=o.name)

    ## select and make cage active
    # cage.select_set(True)
    bpy.context.view_layer.objects.active = cage
    obj.select_set(False) # deselect GP object
    bpy.ops.object.mode_set(mode='EDIT') # go in lattice edit mode
    bpy.ops.lattice.select_all(action='SELECT') # select all points

    if prefs.use_clic_drag:
        ## Eventually change tool mode to tweak for direct point editing (reset after before leaving)
        bpy.ops.wm.tool_set_by_id(name="builtin.select") # Tweaktoolcode
    return cage


def back_to_obj(obj, gp_mode, org_lattice_toolset, context):
    if context.mode == 'EDIT_LATTICE' and org_lattice_toolset: # Tweaktoolcode - restore the active tool used by lattice edit..
        bpy.ops.wm.tool_set_by_id(name = org_lattice_toolset) # Tweaktoolcode

    # gp object active and selected
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def delete_cage(cage):
    lattice = cage.data
    bpy.data.objects.remove(cage)
    bpy.data.lattices.remove(lattice)

def apply_cage(gp_obj, context):
    mod = gp_obj.grease_pencil_modifiers.get('tmp_lattice')
    multi_user = None
    if mod:
        if gp_obj.data.users > 1:
            old = gp_obj.data
            multi_user = old.name
            other_user = [o for o in bpy.data.objects if o is not gp_obj and o.data is old]
            gp_obj.data = gp_obj.data.copy()

        with context.temp_override(object=gp_obj):
            bpy.ops.object.gpencil_modifier_apply(apply_as='DATA', modifier=mod.name)

        if multi_user:
            for o in other_user: # relink
                o.data = gp_obj.data
            bpy.data.grease_pencils.remove(old)
            gp_obj.data.name = multi_user

    else:
        print('tmp_lattice modifier not found to apply...')

def cancel_cage(self):
    #remove modifier
    mod = self.gp_obj.grease_pencil_modifiers.get('tmp_lattice')
    if mod:
        self.gp_obj.grease_pencil_modifiers.remove(mod)
    else:
        print(f'tmp_lattice modifier not found to remove on {self.gp_obj.name}')

    for ob in self.other_gp:
        mod = ob.grease_pencil_modifiers.get('tmp_lattice')
        if mod:
            ob.grease_pencil_modifiers.remove(mod)
        else:
            print(f'tmp_lattice modifier not found to remove on {ob.name}')

    delete_cage(self.cage)


class VIEW3D_OT_gp_box_deform(bpy.types.Operator):
    bl_idname = "view3d.gp_box_deform"
    bl_label = "Box Deform"
    bl_description = "Use lattice for free box transforms on grease pencil points\
        \n(Ctrl+T)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type in ('GPENCIL','LATTICE')

    # local variable
    tab_press_ct = 0

    def modal(self, context, event):
        display_text = f"Deform Cage size: {self.lat.points_u}x{self.lat.points_v} (1-9 or ctrl + ←→↑↓)  | \
mode (M) : {'Linear' if self.lat.interpolation_type_u == 'KEY_LINEAR' else 'Spline'} | \
valid:Spacebar/Enter, cancel:Del/Backspace/Tab/{self.shortcut_ui}"
        context.area.header_text_set(display_text)


        ## Handle ctrl+Z
        if event.type in {'Z'} and event.value == 'PRESS' and event.ctrl:
            ## Disable (capture key)
            return {"RUNNING_MODAL"}
            ## Not found how possible to find modal start point in undo stack to
            # print('ops list', context.window_manager.operators.keys())
            # if context.window_manager.operators:#can be empty
            #     print('\nlast name', context.window_manager.operators[-1].name)

        # Auto interpo check
        if self.auto_interp:
            if event.type in {'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'ZERO',} and event.value == 'PRESS':
                self.set_lattice_interp('KEY_BSPLINE')
            if event.type in {'DOWN_ARROW', "UP_ARROW", "RIGHT_ARROW", "LEFT_ARROW"} and event.value == 'PRESS' and event.ctrl:
                self.set_lattice_interp('KEY_BSPLINE')
            if event.type in {'ONE'} and event.value == 'PRESS':
                self.set_lattice_interp('KEY_LINEAR')

        # Single keys
        if event.type in {'H'} and event.value == 'PRESS':
            # self.report({'INFO'}, "Can't hide")
            return {"RUNNING_MODAL"}

        if event.type in {'ONE'} and event.value == 'PRESS':# , 'NUMPAD_1'
            self.lat.points_u = self.lat.points_v = 2
            return {"RUNNING_MODAL"}

        if event.type in {'TWO'} and event.value == 'PRESS':# , 'NUMPAD_2'
            self.lat.points_u = self.lat.points_v = 3
            return {"RUNNING_MODAL"}

        if event.type in {'THREE'} and event.value == 'PRESS':# , 'NUMPAD_3'
            self.lat.points_u = self.lat.points_v = 4
            return {"RUNNING_MODAL"}

        if event.type in {'FOUR'} and event.value == 'PRESS':# , 'NUMPAD_4'
            self.lat.points_u = self.lat.points_v = 5
            return {"RUNNING_MODAL"}

        if event.type in {'FIVE'} and event.value == 'PRESS':# , 'NUMPAD_5'
            self.lat.points_u = self.lat.points_v = 6
            return {"RUNNING_MODAL"}

        if event.type in {'SIX'} and event.value == 'PRESS':# , 'NUMPAD_6'
            self.lat.points_u = self.lat.points_v = 7
            return {"RUNNING_MODAL"}

        if event.type in {'SEVEN'} and event.value == 'PRESS':# , 'NUMPAD_7'
            self.lat.points_u = self.lat.points_v = 8
            return {"RUNNING_MODAL"}

        if event.type in {'EIGHT'} and event.value == 'PRESS':# , 'NUMPAD_8'
            self.lat.points_u = self.lat.points_v = 9
            return {"RUNNING_MODAL"}

        if event.type in {'NINE'} and event.value == 'PRESS':# , 'NUMPAD_9'
            self.lat.points_u = self.lat.points_v = 10
            return {"RUNNING_MODAL"}

        if event.type in {'ZERO'} and event.value == 'PRESS':# , 'NUMPAD_0'
            self.lat.points_u = 2
            self.lat.points_v = 1
            return {"RUNNING_MODAL"}

        if event.type in {'RIGHT_ARROW'} and event.value == 'PRESS' and event.ctrl:
            if self.lat.points_u < 20:
                self.lat.points_u += 1
            return {"RUNNING_MODAL"}

        if event.type in {'LEFT_ARROW'} and event.value == 'PRESS' and event.ctrl:
            if self.lat.points_u > 1:
                self.lat.points_u -= 1
            return {"RUNNING_MODAL"}

        if event.type in {'UP_ARROW'} and event.value == 'PRESS' and event.ctrl:
            if self.lat.points_v < 20:
                self.lat.points_v += 1
            return {"RUNNING_MODAL"}

        if event.type in {'DOWN_ARROW'} and event.value == 'PRESS' and event.ctrl:
            if self.lat.points_v > 1:
                self.lat.points_v -= 1
            return {"RUNNING_MODAL"}


        # Change modes
        if event.type in {'M'} and event.value == 'PRESS':
            self.auto_interp = False
            interp = 'KEY_BSPLINE' if self.lat.interpolation_type_u == 'KEY_LINEAR' else 'KEY_LINEAR'
            self.set_lattice_interp(interp)
            return {"RUNNING_MODAL"}

        # Valid
        if event.type in {'RET', 'SPACE', 'NUMPAD_ENTER'}:
            if event.value == 'PRESS':
                context.window_manager.boxdeform_running = False
                self.restore_prefs(context)
                back_to_obj(self.gp_obj, self.gp_mode, self.org_lattice_toolset, context)
                if event.shift:
                    # Let the cage as is with a unique ID
                    store_cage(self, 'lattice_cage_deform_group')
                else:
                    apply_cage(self.gp_obj, context) # must be in object mode
                    assign_vg(self.gp_obj, 'lattice_cage_deform_group', delete=True)
                    for o in self.other_gp:
                        apply_cage(o, context)
                        assign_vg(o, 'lattice_cage_deform_group', delete=True)
                    delete_cage(self.cage)

                # back to original mode
                if self.gp_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode=self.gp_mode)
                context.area.header_text_set(None) # Reset header

                return {'FINISHED'}

        # Abort ---
        # One Warning for Tab cancellation.
        if event.type == 'TAB' and event.value == 'PRESS':
            self.tab_press_ct += 1
            if self.tab_press_ct < 2:
                self.report({'WARNING'}, "Pressing TAB again will Cancel")
                return {"RUNNING_MODAL"}


        if all(getattr(event, k) == v for k,v in self.shortcut_d.items()):
            # Cancel when retyped same shortcut
            self.cancel(context)
            return {'CANCELLED'}

        if event.type in {'DEL', 'BACK_SPACE'} or self.tab_press_ct >= 2:#'ESC',
            self.cancel(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def set_lattice_interp(self, interp):
        self.lat.interpolation_type_u = self.lat.interpolation_type_v = self.lat.interpolation_type_w = interp

    def cancel(self, context):
        context.window_manager.boxdeform_running = False
        self.restore_prefs(context)
        back_to_obj(self.gp_obj, self.gp_mode, self.org_lattice_toolset, context)
        cancel_cage(self)
        assign_vg(self.gp_obj, 'lattice_cage_deform_group', delete=True)
        context.area.header_text_set(None)
        if self.gp_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=self.gp_mode)

    def store_prefs(self, context):
        # store_valierables <-< preferences
        self.use_drag_immediately = context.preferences.inputs.use_drag_immediately
        self.drag_threshold_mouse = context.preferences.inputs.drag_threshold_mouse
        self.drag_threshold_tablet = context.preferences.inputs.drag_threshold_tablet
        self.use_overlays = context.space_data.overlay.show_overlays
        # maybe store in windows manager to keep around in case of modal revival ?

    def restore_prefs(self, context):
        # preferences <-< store_valierables
        context.preferences.inputs.use_drag_immediately = self.use_drag_immediately
        context.preferences.inputs.drag_threshold_mouse = self.drag_threshold_mouse
        context.preferences.inputs.drag_threshold_tablet = self.drag_threshold_tablet
        context.space_data.overlay.show_overlays = self.use_overlays

    def set_prefs(self, context):
        context.preferences.inputs.use_drag_immediately = True
        context.preferences.inputs.drag_threshold_mouse = 1
        context.preferences.inputs.drag_threshold_tablet = 3
        context.space_data.overlay.show_overlays = True

    def invoke(self, context, event):
        ## Store cancel shortcut
        if event.type not in ('LEFTMOUSE', 'RIGHTMOUSE') and event.value == 'PRESS':
            self.shortcut_d = {'type': event.type, 'value': event.value, 'ctrl': event.ctrl,
                'shift': event.shift, 'alt': event.alt, 'oskey': event.oskey}
        else:
            self.shortcut_d = {'type': 'T', 'value': 'PRESS', 'ctrl': True,
                'shift': False, 'alt': False, 'oskey': False}
        self.shortcut_ui = '+'.join([k.title() for k,v in self.shortcut_d.items() if v is True] + [self.shortcut_d['type']]) 

        ## Restrict to 3D view
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

        if not context.object:#do it in poll ?
            self.report({'ERROR'}, "No active objects found")
            return {'CANCELLED'}

        if context.window_manager.boxdeform_running:
            return {'CANCELLED'}

        self.prefs = get_addon_prefs()#get_prefs
        self.auto_interp = self.prefs.auto_swap_deform_type
        self.org_lattice_toolset = None
        ## usability toggles
        if self.prefs.use_clic_drag:#Store the active tool since we will change it
            self.org_lattice_toolset = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False).idname# Tweaktoolcode

        #store (scene properties needed in case of ctrlZ revival)
        self.store_prefs(context)
        self.gp_mode = 'EDIT_GPENCIL'

        # --- special Case of lattice revive modal, just after ctrl+Z back into lattice with modal stopped
        if context.mode == 'EDIT_LATTICE' and context.object.name == 'lattice_cage_deform' and len(context.object.vertex_groups):
            self.gp_obj = context.scene.objects.get(context.object.vertex_groups[0].name)
            if not self.gp_obj:
                self.report({'ERROR'}, "/!\\ Box Deform : Cannot find object to target")
                return {'CANCELLED'}
            if not self.gp_obj.grease_pencil_modifiers.get('tmp_lattice'):
                self.report({'ERROR'}, "/!\\ No 'tmp_lattice' modifiers on GP object")
                return {'CANCELLED'}
            self.cage = context.object
            self.lat = self.cage.data
            self.set_prefs(context)

            if self.prefs.use_clic_drag:
                bpy.ops.wm.tool_set_by_id(name="builtin.select")
            context.window_manager.boxdeform_running = True
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        if context.object.type != 'GPENCIL':
            # self.report({'ERROR'}, "Works only on gpencil objects")
            ## silent return
            return {'CANCELLED'}

        if context.mode not in ('EDIT_GPENCIL', 'OBJECT', 'PAINT_GPENCIL'):
            # self.report({'WARNING'}, "Works only in following GPencil modes: object / edit/ paint")# ERROR
            ## silent return
            return {'CANCELLED'}


        # bpy.ops.ed.undo_push(message="Box deform step")#don't work as expected (+ might be obsolete)
        # https://developer.blender.org/D6147 <- undo forget

        self.gp_obj = context.object

        self.from_object = context.mode == 'OBJECT'
        self.all_gps = self.other_gp = []
        if self.from_object:
            self.all_gps = [o for o in bpy.context.selected_objects if o.type == 'GPENCIL']
            self.other_gp = [o for o in self.all_gps if o is not self.gp_obj]

        # Clean potential failed previous job (delete tmp lattice)
        mod = self.gp_obj.grease_pencil_modifiers.get('tmp_lattice')
        if mod:
            print('Deleted remaining lattice modifiers')
            self.gp_obj.grease_pencil_modifiers.remove(mod)

        phantom_obj = context.scene.objects.get('lattice_cage_deform')
        if phantom_obj:
            print('Deleted remaining lattice object')
            delete_cage(phantom_obj)

        if bpy.app.version < (2,93,0):
            if [m for m in self.gp_obj.grease_pencil_modifiers if m.type == 'GP_LATTICE']:
                self.report({'ERROR'}, "Grease pencil object already has a lattice modifier (multi-lattices are enabled in blender 2.93+)")
                return {'CANCELLED'}

        self.gp_mode = context.mode # store mode for restore

        # All good, create lattice and start modal

        # Create lattice (and switch to lattice edit) ----
        self.cage = view_cage(self.gp_obj)
        if isinstance(self.cage, str):#error, cage not created, display error
            self.report({'ERROR'}, self.cage)
            return {'CANCELLED'}

        self.lat = self.cage.data

        self.set_prefs(context)
        context.window_manager.boxdeform_running = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

## --- KEYMAP

addon_keymaps = []
def register_keymaps():
    addon = bpy.context.window_manager.keyconfigs.addon

    km = addon.keymaps.new(name = "Grease Pencil", space_type = "EMPTY", region_type='WINDOW')
    kmi = km.keymap_items.new("view3d.gp_box_deform", type ='T', value = "PRESS", ctrl = True)
    kmi.repeat = False
    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

### --- REGISTER ---

def register():
    if bpy.app.background:
        return
    bpy.types.WindowManager.boxdeform_running = bpy.props.BoolProperty(default=False)
    bpy.utils.register_class(VIEW3D_OT_gp_box_deform)
    register_keymaps()

def unregister():
    if bpy.app.background:
        return
    unregister_keymaps()
    bpy.utils.unregister_class(VIEW3D_OT_gp_box_deform)
    wm = bpy.context.window_manager
    p = 'boxdeform_running'
    if p in wm:
        del wm[p]
