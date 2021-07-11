import bpy

from bpy.types import Operator

from blenderkit.bl_ui_widgets.bl_ui_label import *
from blenderkit.bl_ui_widgets.bl_ui_button import *
# from blenderkit.bl_ui_widgets.bl_ui_checkbox import *
# from blenderkit.bl_ui_widgets.bl_ui_slider import *
# from blenderkit.bl_ui_widgets.bl_ui_up_down import *
from blenderkit.bl_ui_widgets.bl_ui_drag_panel import *
from blenderkit.bl_ui_widgets.bl_ui_draw_op import *
# from blenderkit.bl_ui_widgets.bl_ui_textbox import *
import random
import math

import blenderkit
from blenderkit import ui, paths, utils, search

from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty
)


def draw_callback_tooltip(self, context):
    if self.draw_tooltip:
        wm = bpy.context.window_manager
        sr = wm.get('search results')
        r = sr[self.active_index]
        ui.draw_tooltip_with_author(r, 0, 500)

def get_area_height(self):
    if type(self.context)!= dict:
        self.context = self.context.copy()
    # print(self.context)
    if self.context.get('area') is not None:
        return self.context['area'].height
    # else:
    #     maxw, maxa, region = utils.get_largest_area()
    #     if maxa:
    #         self.context['area'] = maxa
    #         self.context['window'] = maxw
    #         self.context['region'] = region
    #         self.update(self.x,self.y)
    #
    #         return self.context['area'].height
    # print('no area found')
    return 100

BL_UI_Widget.get_area_height = get_area_height


def asset_bar_modal(self, context, event):
    ui_props = bpy.context.scene.blenderkitUI
    if ui_props.turn_off:
        ui_props.turn_off = False
        self.finish()

    if self._finished:
        return {'FINISHED'}

    if context.area:
        context.area.tag_redraw()
    else:
        self.finish()
        return {'FINISHED'}

    if self.handle_widget_events(event):
        return {'RUNNING_MODAL'}

    if event.type in {"ESC"}:
        self.finish()

    if event.type == 'WHEELUPMOUSE':
        self.scroll_offset -= 5
        self.scroll_update()
        return {'RUNNING_MODAL'}
    elif event.type == 'WHEELDOWNMOUSE':
        self.scroll_offset += 5
        self.scroll_update()
        return {'RUNNING_MODAL'}

    if self.check_ui_resized(context):
        self.update_ui_size(context)
        self.update_layout(context)
    return {"PASS_THROUGH"}

def asset_bar_invoke(self, context, event):

    if not self.on_invoke(context, event):
        return {"CANCELLED"}

    args = (self, context)

    self.register_handlers(args, context)

    context.window_manager.modal_handler_add(self)
    return {"RUNNING_MODAL"}

BL_UI_OT_draw_operator.modal = asset_bar_modal
BL_UI_OT_draw_operator.invoke = asset_bar_invoke


def set_mouse_down_right(self, mouse_down_right_func):
    self.mouse_down_right_func = mouse_down_right_func


def mouse_down_right(self, x, y):
    if self.is_in_rect(x, y):
        self.__state = 1
        try:
            self.mouse_down_right_func(self)
        except Exception as e:
            print(e)

        return True

    return False

# def handle_event(self, event):
#     x = event.mouse_region_x
#     y = event.mouse_region_y
#
#     if (event.type == 'LEFTMOUSE'):
#         if (event.value == 'PRESS'):
#             self._mouse_down = True
#             return self.mouse_down(x, y)
#         else:
#             self._mouse_down = False
#             self.mouse_up(x, y)
#
#     elif (event.type == 'RIGHTMOUSE'):
#         if (event.value == 'PRESS'):
#             self._mouse_down_right = True
#             return self.mouse_down_right(x, y)
#         else:
#             self._mouse_down_right = False
#             self.mouse_up(x, y)
#
#     elif (event.type == 'MOUSEMOVE'):
#         self.mouse_move(x, y)
#
#         inrect = self.is_in_rect(x, y)
#
#         # we enter the rect
#         if not self.__inrect and inrect:
#             self.__inrect = True
#             self.mouse_enter(event, x, y)
#
#         # we are leaving the rect
#         elif self.__inrect and not inrect:
#             self.__inrect = False
#             self.mouse_exit(event, x, y)
#
#         return False
#
#     elif event.value == 'PRESS' and (event.ascii != '' or event.type in self.get_input_keys()):
#         return self.text_input(event)
#
#     return False

BL_UI_Button.mouse_down_right = mouse_down_right
BL_UI_Button.set_mouse_down_right = set_mouse_down_right
# BL_UI_Button.handle_event = handle_event




class BlenderKitAssetBarOperator(BL_UI_OT_draw_operator):
    bl_idname = "view3d.blenderkit_asset_bar_widget"
    bl_label = "BlenderKit asset bar refresh"
    bl_description = "BlenderKit asset bar refresh"
    bl_options = {'REGISTER'}

    do_search: BoolProperty(name="Run Search", description='', default=True, options={'SKIP_SAVE'})
    keep_running: BoolProperty(name="Keep Running", description='', default=True, options={'SKIP_SAVE'})
    free_only: BoolProperty(name="Free first", description='', default=False, options={'SKIP_SAVE'})

    category: StringProperty(
        name="Category",
        description="search only subtree of this category",
        default="", options={'SKIP_SAVE'})

    tooltip: bpy.props.StringProperty(default='Runs search and displays the asset bar at the same time')

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def new_text(self, text, x, y, width=100, height=15, text_size=None):
        label = BL_UI_Label(x, y, width, height)
        label.text = text
        if text_size is None:
            text_size = 14
        label.text_size = text_size
        label.text_color = self.text_color
        return label

    def init_tooltip(self):
        self.tooltip_widgets = []
        tooltip_size = 500
        total_size = tooltip_size + 2 * self.assetbar_margin
        self.tooltip_panel = BL_UI_Drag_Panel(0, 0, total_size, total_size)
        self.tooltip_panel.bg_color = (0.0, 0.0, 0.0, 0.5)
        self.tooltip_panel.visible = False

        tooltip_image = BL_UI_Button(self.assetbar_margin, self.assetbar_margin, 1, 1)
        tooltip_image.text = ""
        img_path = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')
        tooltip_image.set_image(img_path)
        tooltip_image.set_image_size((tooltip_size, tooltip_size))
        tooltip_image.set_image_position((0, 0))
        self.tooltip_image = tooltip_image
        self.tooltip_widgets.append(tooltip_image)

        bottom_panel_fraction = 0.1
        labels_start = total_size * (1 - bottom_panel_fraction) - self.margin

        dark_panel = BL_UI_Widget(0, labels_start, total_size, total_size * bottom_panel_fraction)
        dark_panel.bg_color = (0.0, 0.0, 0.0, 0.7)
        self.tooltip_widgets.append(dark_panel)

        name_label = self.new_text('', self.assetbar_margin*2, labels_start, text_size=16)
        self.asset_name = name_label
        self.tooltip_widgets.append(name_label)
        offset_y = 16 + self.margin
        # label = self.new_text('Left click or drag to append/link. Right click for more options.', self.assetbar_margin*2, labels_start + offset_y,
        #                       text_size=14)
        # self.tooltip_widgets.append(label)


        self.hide_tooltip()

    def hide_tooltip(self):
        self.tooltip_panel.visible = False
        for w in self.tooltip_widgets:
            w.visible = False

    def show_tooltip(self):
        self.tooltip_panel.visible = True
        for w in self.tooltip_widgets:
            w.visible = True

    def check_ui_resized(self,context):
        region = context.region
        area = context.area
        ui_props = bpy.context.scene.blenderkitUI
        ui_scale = bpy.context.preferences.view.ui_scale

        reg_multiplier = 1
        if not bpy.context.preferences.system.use_region_overlap:
            reg_multiplier = 0

        for r in area.regions:
            if r.type == 'TOOLS':
                self.bar_x = r.width * reg_multiplier + self.margin + ui_props.bar_x_offset * ui_scale
            elif r.type == 'UI':
                self.bar_end = r.width * reg_multiplier + 100 * ui_scale

        bar_width = region.width - self.bar_x - self.bar_end
        if bar_width != self.bar_width:
            return True
        return False

    def update_ui_size(self, context):

        if bpy.app.background or not context.area:
            return

        region = context.region
        area = context.area

        ui_props = bpy.context.scene.blenderkitUI
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        ui_scale = bpy.context.preferences.view.ui_scale

        self.margin = ui_props.bl_rna.properties['margin'].default * ui_scale
        self.margin = 3
        self.assetbar_margin = self.margin

        self.thumb_size = user_preferences.thumb_size * ui_scale
        self.button_size = 2 * self.margin + self.thumb_size

        reg_multiplier = 1
        if not bpy.context.preferences.system.use_region_overlap:
            reg_multiplier = 0

        for r in area.regions:
            if r.type == 'TOOLS':
                self.bar_x = r.width * reg_multiplier + self.margin + ui_props.bar_x_offset * ui_scale
            elif r.type == 'UI':
                self.bar_end = r.width * reg_multiplier + 100 * ui_scale

        self.bar_width = region.width - self.bar_x - self.bar_end

        self.wcount = math.floor(
            (self.bar_width) / (self.button_size))

        search_results = bpy.context.window_manager.get('search results')
        # we need to init all possible thumb previews in advance/
        self.hcount = user_preferences.max_assetbar_rows
        # if search_results is not None and self.wcount > 0:
        #     self.hcount = min(user_preferences.max_assetbar_rows, math.ceil(len(search_results) / self.wcount))
        # else:
        #     self.hcount = 1

        self.bar_height = (self.button_size) * self.hcount + 2 * self.assetbar_margin
        # self.bar_y = region.height - ui_props.bar_y_offset * ui_scale
        self.bar_y = ui_props.bar_y_offset * ui_scale
        if ui_props.down_up == 'UPLOAD':
            self.reports_y = self.bar_y - 600
            self.reports_x = self.bar_x
        else:
            self.reports_y = self.bar_y - self.bar_height - 100
            self.reports_x = self.bar_x

    def update_layout(self, context):
        pass;

    def __init__(self):
        super().__init__()

        self.update_ui_size(bpy.context)

        ui_props = bpy.context.scene.blenderkitUI

        # todo move all this to update UI size

        self.draw_tooltip = False
        self.scroll_offset = 0

        self.text_color = (0.9, 0.9, 0.9, 1.0)
        button_bg_color = (0.2, 0.2, 0.2, .1)
        button_hover_color = (0.8, 0.8, 0.8, .2)

        self.init_tooltip()

        self.buttons = []
        self.asset_buttons = []
        self.validation_icons = []
        self.widgets_panel = []

        self.panel = BL_UI_Drag_Panel(0, 0, self.bar_width, self.bar_height)
        self.panel.bg_color = (0.0, 0.0, 0.0, 0.5)

        for a in range(0, self.wcount):
            for b in range(0, self.hcount):
                asset_x = self.assetbar_margin + a * (self.button_size)
                asset_y = self.assetbar_margin + b * (self.button_size)
                new_button = BL_UI_Button(asset_x, asset_y, self.button_size, self.button_size)

                asset_idx = a + b * self.wcount + self.scroll_offset
                # asset_data = sr[asset_idx]
                # iname = blenderkit.utils.previmg_name(asset_idx)
                # img = bpy.data.images.get(iname)

                new_button.bg_color = button_bg_color
                new_button.hover_bg_color = button_hover_color
                new_button.text = ""  # asset_data['name']
                # if img:
                #     new_button.set_image(img.filepath)

                new_button.set_image_size((self.thumb_size, self.thumb_size))
                new_button.set_image_position((self.margin, self.margin))
                new_button.button_index = asset_idx
                new_button.search_index = asset_idx
                new_button.set_mouse_down(self.drag_drop_asset)
                new_button.set_mouse_down_right(self.asset_menu)
                new_button.set_mouse_enter(self.enter_button)
                new_button.set_mouse_exit(self.exit_button)
                new_button.text_input = self.handle_key_input
                self.asset_buttons.append(new_button)
                # add validation icon to button
                icon_size = 24
                validation_icon = BL_UI_Button(asset_x + self.button_size - icon_size - self.margin,
                                                 asset_y + self.button_size - icon_size - self.margin, 0, 0)

                # v_icon = ui.verification_icons[asset_data.get('verificationStatus', 'validated')]
                # if v_icon is not None:
                #     img_fp = paths.get_addon_thumbnail_path(v_icon)
                #     validation_icon.set_image(img_fp)
                validation_icon.text = ''
                validation_icon.set_image_size((icon_size, icon_size))
                validation_icon.set_image_position((0, 0))
                self.validation_icons.append(validation_icon)
                new_button.validation_icon = validation_icon

        other_button_size = 30

        self.button_close = BL_UI_Button(self.bar_width - other_button_size, -0, other_button_size, 15)
        self.button_close.bg_color = button_bg_color
        self.button_close.hover_bg_color = button_hover_color
        self.button_close.text = "x"
        self.button_close.set_mouse_down(self.cancel_press)

        self.widgets_panel.append(self.button_close)
        scroll_width = 30
        self.button_scroll_down = BL_UI_Button(-scroll_width, 0, scroll_width, self.bar_height)
        self.button_scroll_down.bg_color = button_bg_color
        self.button_scroll_down.hover_bg_color = button_hover_color
        self.button_scroll_down.text = ""
        self.button_scroll_down.set_image(paths.get_addon_thumbnail_path('arrow_left.png'))
        self.button_scroll_down.set_image_size((scroll_width, self.button_size))
        self.button_scroll_down.set_image_position((0, int((self.bar_height - self.button_size) / 2)))

        self.button_scroll_down.set_mouse_down(self.scroll_down)

        self.widgets_panel.append(self.button_scroll_down)

        self.button_scroll_up = BL_UI_Button(self.bar_width, 0, scroll_width, self.bar_height)
        self.button_scroll_up.bg_color = button_bg_color
        self.button_scroll_up.hover_bg_color = button_hover_color
        self.button_scroll_up.text = ""
        self.button_scroll_up.set_image(paths.get_addon_thumbnail_path('arrow_right.png'))
        self.button_scroll_up.set_image_size((scroll_width, self.button_size))
        self.button_scroll_up.set_image_position((0, int((self.bar_height - self.button_size) / 2)))

        self.button_scroll_up.set_mouse_down(self.scroll_up)

        self.widgets_panel.append(self.button_scroll_up)

        self.update_images()

    def on_invoke(self, context, event):


        if self.do_search:
            #TODO: move the search behaviour to separate operator, since asset bar can be already woken up from a timer.

            # we erase search keywords for cateogry search now, since these combinations usually return nothing now.
            # when the db gets bigger, this can be deleted.
            if self.category != '':
                sprops = utils.get_search_props()
                sprops.search_keywords = ''
            search.search(category=self.category)

        ui_props = context.scene.blenderkitUI
        if ui_props.assetbar_on:
            #TODO solve this otehrwise to enable more asset bars?

            # we don't want to run the assetbar many times, that's why it has a switch on/off behaviour,
            # unless being called with 'keep_running' prop.
            if not self.keep_running:
                # this sends message to the originally running operator, so it quits, and then it ends this one too.
                # If it initiated a search, the search will finish in a thread. The switch off procedure is run
                # by the 'original' operator, since if we get here, it means
                # same operator is already running.
                ui_props.turn_off = True
                # if there was an error, we need to turn off these props so we can restart after 2 clicks
                ui_props.assetbar_on = False

            else:
                pass
            return False

        ui_props.assetbar_on =  True

        self.active_index = -1

        widgets_panel = self.widgets_panel
        widgets_panel.extend(self.buttons)
        widgets_panel.extend(self.asset_buttons)
        widgets_panel.extend(self.validation_icons)

        widgets = [self.panel]

        widgets += widgets_panel
        widgets.append(self.tooltip_panel)
        widgets += self.tooltip_widgets

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)
        self.tooltip_panel.add_widgets(self.tooltip_widgets)

        # Open the panel at the mouse location
        # self.panel.set_location(bpy.context.area.width - event.mouse_x,
        #                         bpy.context.area.height - event.mouse_y + 20)
        self.panel.set_location(self.bar_x,
                                self.bar_y)

        self.context = context
        args = (self, context)

        # self._handle_2d_tooltip = bpy.types.SpaceView3D.draw_handler_add(draw_callback_tooltip, args, 'WINDOW', 'POST_PIXEL')
        return True

    def on_finish(self, context):
        # redraw all areas, since otherwise it stays to hang for some more time.
        # bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d_tooltip, 'WINDOW')

        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        ui_props.assetbar_on = False

        wm = bpy.data.window_managers[0]

        for w in wm.windows:
            for a in w.screen.areas:
                a.tag_redraw()

        self._finished = True

    # handlers

    def enter_button(self, widget):
        # context.window.cursor_warp(event.mouse_x, event.mouse_y - 20);


        self.show_tooltip()

        if self.active_index != widget.search_index:
            scene = bpy.context.scene
            wm = bpy.context.window_manager
            sr = wm['search results']
            asset_data = sr[widget.search_index + self.scroll_offset]

            self.active_index = widget.search_index
            self.draw_tooltip = True
            self.tooltip = asset_data['tooltip']
            ui_props = scene.blenderkitUI
            ui_props.active_index = widget.search_index +self.scroll_offset

            img = ui.get_large_thumbnail_image(asset_data)
            if img:
                self.tooltip_image.set_image(img.filepath)
            self.asset_name.text = asset_data['name']

            properties_width = 0
            for r in bpy.context.area.regions:
                if r.type == 'UI':
                    properties_width = r.width
            tooltip_x = min(widget.x_screen + widget.width, bpy.context.region.width - self.tooltip_panel.width -properties_width)

            self.tooltip_panel.update(tooltip_x, widget.y_screen + widget.height)
            self.tooltip_panel.layout_widgets()
            # bpy.ops.wm.blenderkit_asset_popup('INVOKE_DEFAULT')


    def exit_button(self, widget):
        # this condition checks if there wasn't another button already entered, which can happen with small button gaps
        if self.active_index == widget.search_index:
            scene = bpy.context.scene
            ui_props = scene.blenderkitUI
            ui_props.draw_tooltip = False
            self.draw_tooltip = False
            self.hide_tooltip()

    def drag_drop_asset(self, widget):
        bpy.ops.view3d.asset_drag_drop('INVOKE_DEFAULT', asset_search_index=widget.search_index + self.scroll_offset)

    def cancel_press(self, widget):
        self.finish()

    def asset_menu(self, widget):
        bpy.ops.wm.blenderkit_asset_popup('INVOKE_DEFAULT')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_asset_menu')

    def search_more(self):
        sro = bpy.context.window_manager.get('search results orig')
        if sro is not None and sro.get('next') is not None:
            blenderkit.search.search(get_next=True)

    def update_images(self):
        sr = bpy.context.window_manager.get('search results')
        if not sr:
            return
        for asset_button in self.asset_buttons:
            asset_button.asset_index = asset_button.button_index + self.scroll_offset
            if asset_button.asset_index < len(sr):
                asset_button.visible = True

                asset_data = sr[asset_button.asset_index]

                iname = blenderkit.utils.previmg_name(asset_button.asset_index)
                # show indices for debug purposes
                # asset_button.text = str(asset_button.asset_index)
                img = bpy.data.images.get(iname)
                if not img:
                    img_filepath = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')
                else:
                    img_filepath = img.filepath
                asset_button.set_image(img_filepath)
                v_icon = ui.verification_icons[asset_data.get('verificationStatus', 'validated')]
                if v_icon is not None:
                    img_fp = paths.get_addon_thumbnail_path(v_icon)
                    asset_button.validation_icon.set_image(img_fp)
                    asset_button.validation_icon.visible = True
                else:
                    asset_button.validation_icon.visible = False
            else:
                asset_button.visible = False
                asset_button.validation_icon.visible = False

    def scroll_update(self):
        sr = bpy.context.window_manager['search results']
        self.scroll_offset = min(self.scroll_offset, len(sr) - (self.wcount * self.hcount))
        self.scroll_offset = max(self.scroll_offset, 0)
        self.update_images()
        if len(sr) - self.scroll_offset < (self.wcount * self.hcount) + 10:
            self.search_more()

    def search_by_author(self, asset_index):
        sr = bpy.context.window_manager['search results']
        asset_data = sr[asset_index]
        a = asset_data['author']['id']
        if a is not None:
            sprops = utils.get_search_props()
            sprops.search_keywords = ''
            sprops.search_verification_status = 'ALL'
            utils.p('author:', a)
            search.search(author_id=a)
        return True

    def handle_key_input(self, event):
        if event.type == 'A':
            self.search_by_author(self.active_index + self.scroll_offset)
        return False

    def scroll_up(self, widget):
        self.scroll_offset += self.wcount * self.hcount
        self.scroll_update()

    def scroll_down(self, widget):
        self.scroll_offset -= self.wcount * self.hcount
        self.scroll_update()

    def update_sizes(self):
        properties_width = 0
        for r in bpy.context.area.regions:
            if r.type == 'UI':
                properties_width = r.width
        tooltip_x = min(widget.x_screen + widget.width,
                        bpy.context.region.width - self.tooltip_panel.width - properties_width)
        # print(widget.x_screen + widget.width, bpy.context.region.width - self.tooltip_panel.width)


def register():
    bpy.utils.register_class(BlenderKitAssetBarOperator)


def unregister():
    bpy.utils.unregister_class(BlenderKitAssetBarOperator)
