import bpy

from bpy.types import Operator

from blenderkit.bl_ui_widgets.bl_ui_label import *
from blenderkit.bl_ui_widgets.bl_ui_button import *
from blenderkit.bl_ui_widgets.bl_ui_image import *
# from blenderkit.bl_ui_widgets.bl_ui_checkbox import *
# from blenderkit.bl_ui_widgets.bl_ui_slider import *
# from blenderkit.bl_ui_widgets.bl_ui_up_down import *
from blenderkit.bl_ui_widgets.bl_ui_drag_panel import *
from blenderkit.bl_ui_widgets.bl_ui_draw_op import *
# from blenderkit.bl_ui_widgets.bl_ui_textbox import *
import random
import math
import time

import blenderkit
from blenderkit import ui, paths, utils, search, comments_utils

from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty
)

active_area_pointer = 0

def get_area_height(self):
    if type(self.context) != dict:
        if self.context is None:
            self.context = bpy.context
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


def modal_inside(self, context, event):
    ui_props = bpy.context.window_manager.blenderkitUI
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

    self.update_timer += 1

    if self.update_timer > self.update_timer_limit:
        self.update_timer = 0
        # print('timer', time.time())
        self.update_images()

        # progress bar
        sr = bpy.context.window_manager.get('search results')
        ui_scale = bpy.context.preferences.view.ui_scale
        for asset_button in self.asset_buttons:
            if sr is not None and len(sr) > asset_button.asset_index:
                asset_data = sr[asset_button.asset_index]

                if asset_data['downloaded'] > 0:
                    asset_button.progress_bar.width = int(self.button_size * ui_scale * asset_data['downloaded'] / 100)
                    asset_button.progress_bar.visible = True
                else:
                    asset_button.progress_bar.visible = False

    if self.handle_widget_events(event):
        return {'RUNNING_MODAL'}

    if event.type in {"ESC"}:
        self.finish()

    self.mouse_x = event.mouse_region_x
    self.mouse_y = event.mouse_region_y
    if event.type == 'WHEELUPMOUSE' and self.panel.is_in_rect(self.mouse_x, self.mouse_y):
        self.scroll_offset -= 2
        self.scroll_update()
        return {'RUNNING_MODAL'}

    elif event.type == 'WHEELDOWNMOUSE' and self.panel.is_in_rect(self.mouse_x, self.mouse_y):
        self.scroll_offset += 2
        self.scroll_update()
        return {'RUNNING_MODAL'}

    if self.check_ui_resized(context) or self.check_new_search_results(context):
        # print(self.check_ui_resized(context), print(self.check_new_search_results(context)))
        self.update_ui_size(context)
        self.update_layout(context, event)

    return {"PASS_THROUGH"}


def asset_bar_modal(self, context, event):
    return modal_inside(self, context, event)


def asset_bar_invoke(self, context, event):
    if not self.on_invoke(context, event):
        return {"CANCELLED"}

    args = (self, context)

    self.register_handlers(args, context)

    self.update_timer_limit = 30
    self.update_timer = 0
    # print('adding timer')
    # self._timer = context.window_manager.event_timer_add(10.0, window=context.window)
    global active_area_pointer
    context.window_manager.modal_handler_add(self)
    self.active_window_pointer = context.window.as_pointer()
    self.active_area_pointer = context.area.as_pointer()
    active_area_pointer = context.area.as_pointer()
    self.active_region_pointer = context.region.as_pointer()

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


BL_UI_Button.mouse_down_right = mouse_down_right
BL_UI_Button.set_mouse_down_right = set_mouse_down_right

asset_bar_operator = None


# BL_UI_Button.handle_event = handle_event

def get_tooltip_data(asset_data):
    gimg = None
    tooltip_data = asset_data.get('tooltip_data')
    if tooltip_data is None:
        author_text = ''

        if bpy.context.window_manager.get('bkit authors') is not None:
            a = bpy.context.window_manager['bkit authors'].get(asset_data['author']['id'])
            if a is not None and a != '':
                if a.get('gravatarImg') is not None:
                    gimg = utils.get_hidden_image(a['gravatarImg'], a['gravatarHash']).name

                if len(a['firstName']) > 0 or len(a['lastName']) > 0:
                    author_text = f"by {a['firstName']} {a['lastName']}"

        aname = asset_data['displayName']
        aname = aname[0].upper() + aname[1:]
        if len(aname) > 36:
            aname = f"{aname[:33]}..."

        rc = asset_data.get('ratingsCount')
        show_rating_threshold = 0
        rcount = 0
        quality = '-'
        if rc:
            rcount = min(rc.get('quality', 0), rc.get('workingHours', 0))
        if rcount > show_rating_threshold:
            quality = str(round(asset_data['ratingsAverage'].get('quality')))
        tooltip_data = {
            'aname': aname,
            'author_text': author_text,
            'quality': quality,
            'gimg': gimg
        }
        asset_data['tooltip_data'] = tooltip_data
    gimg = tooltip_data['gimg']
    if gimg is not None:
        gimg = bpy.data.images[gimg]


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

    def new_text(self, text, x, y, width=100, height=15, text_size=None, halign='LEFT'):
        label = BL_UI_Label(x, y, width, height)
        label.text = text
        if text_size is None:
            text_size = 14
        label.text_size = text_size
        label.text_color = self.text_color
        label._halign = halign
        return label

    def init_tooltip(self):
        self.tooltip_widgets = []
        self.tooltip_height = self.tooltip_size
        self.tooltip_width = self.tooltip_size
        ui_props = bpy.context.window_manager.blenderkitUI
        if ui_props.asset_type == 'HDR':
            self.tooltip_width = self.tooltip_size * 2
        # total_size = tooltip# + 2 * self.margin
        self.tooltip_panel = BL_UI_Drag_Panel(0, 0, self.tooltip_width, self.tooltip_height)
        self.tooltip_panel.bg_color = (0.0, 0.0, 0.0, 0.5)
        self.tooltip_panel.visible = False

        tooltip_image = BL_UI_Image(0, 0, 1, 1)
        img_path = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')
        tooltip_image.set_image(img_path)
        tooltip_image.set_image_size((self.tooltip_width, self.tooltip_height))
        tooltip_image.set_image_position((0, 0))
        self.tooltip_image = tooltip_image
        self.tooltip_widgets.append(tooltip_image)

        bottom_panel_fraction = 0.15
        labels_start = self.tooltip_height * (1 - bottom_panel_fraction)

        dark_panel = BL_UI_Widget(0, labels_start, self.tooltip_width, self.tooltip_height * bottom_panel_fraction)
        dark_panel.bg_color = (0.0, 0.0, 0.0, 0.7)
        self.tooltip_dark_panel = dark_panel
        self.tooltip_widgets.append(dark_panel)

        name_label = self.new_text('', self.margin, labels_start + self.margin,
                                   text_size=self.asset_name_text_size)
        self.asset_name = name_label
        self.tooltip_widgets.append(name_label)

        self.gravatar_size = int(self.tooltip_height * bottom_panel_fraction - self.margin)

        authors_name = self.new_text('author', self.tooltip_width - self.gravatar_size - self.margin,
                                     self.tooltip_height - self.author_text_size - self.margin, labels_start,
                                     text_size=self.author_text_size, halign='RIGHT')
        self.authors_name = authors_name
        self.tooltip_widgets.append(authors_name)

        gravatar_image = BL_UI_Image(self.tooltip_width - self.gravatar_size, self.tooltip_height - self.gravatar_size,
                                     1, 1)
        img_path = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')
        gravatar_image.set_image(img_path)
        gravatar_image.set_image_size((self.gravatar_size - 1 * self.margin, self.gravatar_size - 1 * self.margin))
        gravatar_image.set_image_position((0, 0))
        self.gravatar_image = gravatar_image
        self.tooltip_widgets.append(gravatar_image)

        quality_star = BL_UI_Image(self.margin, self.tooltip_height - self.margin - self.asset_name_text_size,
                                     1, 1)
        img_path = paths.get_addon_thumbnail_path('star_grey.png')
        quality_star.set_image(img_path)
        quality_star.set_image_size((self.asset_name_text_size, self.asset_name_text_size))
        quality_star.set_image_position((0, 0))
        # self.quality_star = quality_star
        self.tooltip_widgets.append(quality_star)
        label = self.new_text('', 2*self.margin+self.asset_name_text_size,
                              self.tooltip_height - int(self.asset_name_text_size+ self.margin * .5),
                              text_size=self.asset_name_text_size)
        self.tooltip_widgets.append(label)
        self.quality_label = label

        # label = self.new_text('Right click for menu.', self.margin,
        #                       self.tooltip_height - int(self.author_text_size) - self.margin,
        #                       text_size=int(self.author_text_size*.7))
        # self.tooltip_widgets.append(label)

    def hide_tooltip(self):
        self.tooltip_panel.visible = False
        for w in self.tooltip_widgets:
            w.visible = False

    def show_tooltip(self):
        self.tooltip_panel.visible = True
        for w in self.tooltip_widgets:
            w.visible = True

    def show_notifications(self, widget):
        bpy.ops.wm.show_notifications()
        if comments_utils.check_notifications_read():
            widget.visible = False

    def check_new_search_results(self, context):
        sr = bpy.context.window_manager.get('search results')
        if not hasattr(self, 'search_results_count'):
            if not sr:
                self.search_results_count = 0
                return True

            self.search_results_count = len(sr)

        if sr is not None and len(sr) != self.search_results_count:
            self.search_results_count = len(sr)
            return True
        return False

    def get_region_size(self, context):
        # just check the size of region..

        region = context.region
        area = context.area
        ui_width = 0
        tools_width = 0
        for r in area.regions:
            if r.type == 'UI':
                ui_width = r.width
            if r.type == 'TOOLS':
                tools_width = r.width
        total_width = region.width - tools_width - ui_width
        return total_width, region.height

    def check_ui_resized(self, context):
        # TODO this should only check if region was resized, not really care about the UI elements size.
        region_width, region_height = self.get_region_size(context)

        if not hasattr(self, 'total_width'):
            self.total_width = region_width
            self.region_height = region_height

        if region_height != self.region_height or region_width != self.total_width:
            self.region_height = region_height
            self.total_width = region_width
            return True
        return False

    def update_ui_size(self, context):

        if bpy.app.background or not context.area:
            return

        region = context.region
        area = context.area

        ui_props = bpy.context.window_manager.blenderkitUI
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        ui_scale = bpy.context.preferences.view.ui_scale

        self.margin = ui_props.bl_rna.properties['margin'].default * ui_scale
        self.margin = int(9 * ui_scale)
        self.button_margin = int(0 * ui_scale)
        self.asset_name_text_size = int(20 * ui_scale)
        self.author_text_size = int(self.asset_name_text_size * .7 * ui_scale)
        self.assetbar_margin = int(2 * ui_scale)
        self.tooltip_size = int(512 * ui_scale)

        if ui_props.asset_type == 'HDR':
            self.tooltip_width = self.tooltip_size * 2
        else:
            self.tooltip_width = self.tooltip_size

        self.thumb_size = user_preferences.thumb_size * ui_scale
        self.button_size = 2 * self.button_margin + self.thumb_size
        self.other_button_size = 30 * ui_scale
        self.icon_size = 24 * ui_scale
        self.validation_icon_margin = 3 * ui_scale
        reg_multiplier = 1
        if not bpy.context.preferences.system.use_region_overlap:
            reg_multiplier = 0

        ui_width = 0
        tools_width = 0
        reg_multiplier = 1
        if not bpy.context.preferences.system.use_region_overlap:
            reg_multiplier = 0
        for r in area.regions:
            if r.type == 'UI':
                ui_width = r.width * reg_multiplier
            if r.type == 'TOOLS':
                tools_width = r.width * reg_multiplier
        self.bar_x = tools_width + self.margin + ui_props.bar_x_offset * ui_scale
        self.bar_end = ui_width + 180 * ui_scale + self.other_button_size
        self.bar_width = region.width - self.bar_x - self.bar_end

        self.wcount = math.floor((self.bar_width) / (self.button_size))

        self.max_hcount = math.floor(context.window.width / self.button_size)
        self.max_wcount = user_preferences.max_assetbar_rows

        search_results = bpy.context.window_manager.get('search results')
        # we need to init all possible thumb previews in advance/
        # self.hcount = user_preferences.max_assetbar_rows
        if search_results is not None and self.wcount > 0:
            self.hcount = min(user_preferences.max_assetbar_rows, math.ceil(len(search_results) / self.wcount))
            self.hcount = max(self.hcount, 1)
        else:
            self.hcount = 1

        self.bar_height = (self.button_size) * self.hcount + 2 * self.assetbar_margin
        # self.bar_y = region.height - ui_props.bar_y_offset * ui_scale
        self.bar_y = ui_props.bar_y_offset * ui_scale
        if ui_props.down_up == 'UPLOAD':
            self.reports_y = region.height - self.bar_y - 600
            ui_props.reports_y = region.height - self.bar_y - 600
            self.reports_x = self.bar_x
            ui_props.reports_x = self.bar_x
        else:#ui.bar_y - ui.bar_height - 100

            self.reports_y = region.height - self.bar_y - self.bar_height - 50
            ui_props.reports_y =region.height -  self.bar_y - self.bar_height- 50
            self.reports_x = self.bar_x
            ui_props.reports_x = self.bar_x
            # print(self.bar_y, self.bar_height, region.height)

    def update_layout(self, context, event):
        # restarting asset_bar completely since the widgets are too hard to get working with updates.

        self.position_and_hide_buttons()

        self.button_close.set_location(self.bar_width - self.other_button_size, -self.other_button_size)
        if hasattr(self, 'button_notifications'):
            self.button_notifications.set_location(self.bar_width - self.other_button_size * 2, -self.other_button_size)
        self.button_scroll_up.set_location(self.bar_width, 0)
        self.panel.width = self.bar_width
        self.panel.height = self.bar_height

        self.panel.set_location(self.bar_x, self.panel.y)

        # update Tooltip size
        if self.tooltip_dark_panel.width != self.tooltip_width:
            self.tooltip_dark_panel.width = self.tooltip_width
            self.tooltip_panel.width = self.tooltip_width
            self.tooltip_image.width = self.tooltip_width
            self.tooltip_image.set_image_size((self.tooltip_width, self.tooltip_height))
            self.gravatar_image.set_location(self.tooltip_width - self.gravatar_size,
                                             self.tooltip_height - self.gravatar_size)
            self.authors_name.set_location(self.tooltip_width - self.gravatar_size - self.margin,
                                           self.tooltip_height - self.author_text_size - self.margin)

        # to hide arrows accordingly
        self.scroll_update()

    def asset_button_init(self, asset_x, asset_y, button_idx):
        ui_scale = bpy.context.preferences.view.ui_scale

        button_bg_color = (0.2, 0.2, 0.2, .1)
        button_hover_color = (0.8, 0.8, 0.8, .2)

        new_button = BL_UI_Button(asset_x, asset_y, self.button_size, self.button_size)

        # asset_data = sr[asset_idx]
        # iname = blenderkit.utils.previmg_name(asset_idx)
        # img = bpy.data.images.get(iname)

        new_button.bg_color = button_bg_color
        new_button.hover_bg_color = button_hover_color
        new_button.text = ""  # asset_data['name']
        # if img:
        #     new_button.set_image(img.filepath)

        new_button.set_image_size((self.thumb_size, self.thumb_size))
        new_button.set_image_position((self.button_margin, self.button_margin))
        new_button.button_index = button_idx
        new_button.search_index = button_idx
        new_button.set_mouse_down(self.drag_drop_asset)
        new_button.set_mouse_down_right(self.asset_menu)
        new_button.set_mouse_enter(self.enter_button)
        new_button.set_mouse_exit(self.exit_button)
        new_button.text_input = self.handle_key_input
        # add validation icon to button

        validation_icon = BL_UI_Image(
            asset_x + self.button_size - self.icon_size - self.button_margin - self.validation_icon_margin,
            asset_y + self.button_size - self.icon_size - self.button_margin - self.validation_icon_margin, 0, 0)

        # v_icon = ui.verification_icons[asset_data.get('verificationStatus', 'validated')]
        # if v_icon is not None:
        #     img_fp = paths.get_addon_thumbnail_path(v_icon)
        #     validation_icon.set_image(img_fp)
        validation_icon.set_image_size((self.icon_size, self.icon_size))
        validation_icon.set_image_position((0, 0))
        self.validation_icons.append(validation_icon)
        new_button.validation_icon = validation_icon

        progress_bar = BL_UI_Widget(asset_x, asset_y + self.button_size - 3, self.button_size, 3)
        progress_bar.bg_color = (0.0, 1.0, 0.0, 0.3)
        new_button.progress_bar = progress_bar
        self.progress_bars.append(progress_bar)

        if utils.profile_is_validator():
            red_alert = BL_UI_Widget(asset_x, asset_y, self.button_size, self.button_size)
            red_alert.bg_color = (1.0, 0.0, 0.0, 0.0)
            red_alert.visible = False
            new_button.red_alert = red_alert
            self.red_alerts.append(red_alert)
        # if result['downloaded'] > 0:
        #     ui_bgl.draw_rect(x, y, int(ui_props.thumb_size * result['downloaded'] / 100.0), 2, green)

        return new_button

    def init_ui(self):
        ui_scale = bpy.context.preferences.view.ui_scale

        button_bg_color = (0.2, 0.2, 0.2, .1)
        button_hover_color = (0.8, 0.8, 0.8, .2)

        self.buttons = []
        self.asset_buttons = []
        self.validation_icons = []
        self.progress_bars = []
        self.red_alerts = []
        self.widgets_panel = []

        self.panel = BL_UI_Drag_Panel(0, 0, self.bar_width, self.bar_height)
        self.panel.bg_color = (0.0, 0.0, 0.0, 0.5)

        # sr = bpy.context.window_manager.get('search results', [])
        # if sr is not None:
        # we init max possible buttons.
        button_idx = 0
        for x in range(0, self.max_wcount):
            for y in range(0, self.max_hcount):
                # asset_x = self.assetbar_margin + a * (self.button_size)
                # asset_y = self.assetbar_margin + b * (self.button_size)
                # button_idx = x + y * self.max_wcount
                asset_idx = button_idx + self.scroll_offset
                # if asset_idx < len(sr):
                new_button = self.asset_button_init(0, 0, button_idx)
                new_button.asset_index = asset_idx
                self.asset_buttons.append(new_button)
                button_idx += 1

        self.button_close = BL_UI_Button(self.bar_width - self.other_button_size, -self.other_button_size,
                                         self.other_button_size,
                                         self.other_button_size)
        self.button_close.bg_color = button_bg_color
        self.button_close.hover_bg_color = button_hover_color
        self.button_close.text = ""
        img_fp = paths.get_addon_thumbnail_path('vs_rejected.png')
        self.button_close.set_image(img_fp)
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

        # notifications
        if not comments_utils.check_notifications_read():
            self.button_notifications = BL_UI_Button(self.bar_width - self.other_button_size * 2,
                                                     -self.other_button_size, self.other_button_size,
                                                     self.other_button_size)
            self.button_notifications.bg_color = button_bg_color
            self.button_notifications.hover_bg_color = button_hover_color
            self.button_notifications.text = ""
            img_fp = paths.get_addon_thumbnail_path('bell.png')
            self.button_notifications.set_image(img_fp)
            self.button_notifications.set_mouse_down(self.show_notifications)
            self.widgets_panel.append(self.button_notifications)

        self.update_images()

    def position_and_hide_buttons(self):
        # position and layout buttons
        sr = bpy.context.window_manager.get('search results', [])
        if sr is None:
            sr = []

        i = 0
        for y in range(0, self.hcount):
            for x in range(0, self.wcount):
                asset_x = self.assetbar_margin + x * (self.button_size)
                asset_y = self.assetbar_margin + y * (self.button_size)
                button_idx = x + y * self.wcount
                asset_idx = button_idx + self.scroll_offset
                if len(self.asset_buttons) <= button_idx:
                    break
                button = self.asset_buttons[button_idx]
                button.set_location(asset_x, asset_y)
                button.validation_icon.set_location(
                    asset_x + self.button_size - self.icon_size - self.button_margin - self.validation_icon_margin,
                    asset_y + self.button_size - self.icon_size - self.button_margin - self.validation_icon_margin)
                button.progress_bar.set_location(asset_x, asset_y + self.button_size - 3)
                if asset_idx < len(sr):
                    button.visible = True
                    button.validation_icon.visible = True
                    # button.progress_bar.visible = True
                else:
                    button.visible = False
                    button.validation_icon.visible = False
                    button.progress_bar.visible = False
                if utils.profile_is_validator():
                    button.red_alert.set_location(asset_x, asset_y)
                i += 1

        for a in range(i, len(self.asset_buttons)):
            button = self.asset_buttons[a]
            button.visible = False
            button.validation_icon.visible = False
            button.progress_bar.visible = False

    def __init__(self):
        super().__init__()

        self.update_ui_size(bpy.context)

        # todo move all this to update UI size
        ui_props = bpy.context.window_manager.blenderkitUI

        self.draw_tooltip = False
        # let's take saved scroll offset and use it to keep scroll between operator runs
        self.scroll_offset = ui_props.scroll_offset

        self.text_color = (0.9, 0.9, 0.9, 1.0)

        self.init_ui()
        self.init_tooltip()
        self.hide_tooltip()

    def setup_widgets(self, context, event):
        widgets_panel = []
        widgets_panel.extend(self.widgets_panel)
        widgets_panel.extend(self.buttons)
        widgets_panel.extend(self.asset_buttons)
        widgets_panel.extend(self.validation_icons)
        widgets_panel.extend(self.progress_bars)
        widgets_panel.extend(self.red_alerts)

        widgets = [self.panel]

        widgets += widgets_panel
        widgets.append(self.tooltip_panel)
        widgets += self.tooltip_widgets

        self.init_widgets(context, widgets)
        self.panel.add_widgets(widgets_panel)
        self.tooltip_panel.add_widgets(self.tooltip_widgets)

    def on_invoke(self, context, event):

        self.context = context

        if self.do_search or context.window_manager.get('search results') is None:
            # TODO: move the search behaviour to separate operator, since asset bar can be already woken up from a timer.

            # we erase search keywords for cateogry search now, since these combinations usually return nothing now.
            # when the db gets bigger, this can be deleted.
            if self.category != '':
                sprops = utils.get_search_props()
                sprops.search_keywords = ''
            search.search(category=self.category)

        ui_props = context.window_manager.blenderkitUI
        if ui_props.assetbar_on:
            # TODO solve this otehrwise to enable more asset bars?

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

        ui_props.assetbar_on = True
        global asset_bar_operator

        asset_bar_operator = self

        self.active_index = -1

        self.setup_widgets(context, event)
        self.position_and_hide_buttons()
        self.hide_tooltip()

        self.panel.set_location(self.bar_x,
                                self.bar_y)
        # to hide arrows accordingly
        self.scroll_update()

        self.window = context.window
        self.area = context.area
        self.scene = bpy.context.scene
        # global active_window_pointer, active_area_pointer, active_region_pointer
        # ui.active_window_pointer = self.window.as_pointer()
        # ui.active_area_pointer = self.area.as_pointer()
        # ui.active_region_pointer = self.region.as_pointer()

        return True

    def on_finish(self, context):
        # redraw all areas, since otherwise it stays to hang for some more time.
        # bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d_tooltip, 'WINDOW')
        # to pass the operator to validation icons
        global asset_bar_operator
        asset_bar_operator = None

        # context.window_manager.event_timer_remove(self._timer)

        scene = bpy.context.scene
        ui_props = bpy.context.window_manager.blenderkitUI
        ui_props.assetbar_on = False
        ui_props.scroll_offset = self.scroll_offset

        wm = bpy.data.window_managers[0]

        for w in wm.windows:
            for a in w.screen.areas:
                a.tag_redraw()
        self._finished = True

    # handlers

    def enter_button(self, widget):
        # print('enter button', self.active_index, widget.button_index)
        # print(widget.button_index+ self.scroll_offset, self.active_index)
        search_index = widget.button_index + self.scroll_offset
        if search_index < self.search_results_count:
            self.show_tooltip()
        # print(self.active_index, search_index)
        if self.active_index != search_index:
            self.active_index = search_index

            scene = bpy.context.scene
            wm = bpy.context.window_manager
            sr = wm['search results']
            asset_data = sr[search_index]  # + self.scroll_offset]

            self.draw_tooltip = True
            # self.tooltip = asset_data['tooltip']
            ui_props = bpy.context.window_manager.blenderkitUI
            ui_props.active_index = search_index  # + self.scroll_offset

            img = ui.get_large_thumbnail_image(asset_data)
            if img:
                self.tooltip_image.set_image(img.filepath)

            get_tooltip_data(asset_data)
            self.asset_name.text = asset_data['name']
            self.authors_name.text = asset_data['tooltip_data']['author_text']
            self.quality_label.text = asset_data['tooltip_data']['quality']
            # print(asset_data['tooltip_data']['quality'])
            gimg = asset_data['tooltip_data']['gimg']
            if gimg is not None:
                gimg = bpy.data.images[gimg]
            if gimg:
                self.gravatar_image.set_image(gimg.filepath
                                              )
            # print('moving tooltip')
            properties_width = 0
            for r in bpy.context.area.regions:
                if r.type == 'UI':
                    properties_width = r.width
            tooltip_x = min(int(widget.x_screen),
                            int(bpy.context.region.width - self.tooltip_panel.width - properties_width))
            tooltip_y = int(widget.y_screen + widget.height)
            # self.init_tooltip()
            self.tooltip_panel.set_location(tooltip_x, tooltip_y)
            self.tooltip_panel.layout_widgets()
            # print(tooltip_x, tooltip_y)
            # bpy.ops.wm.blenderkit_asset_popup('INVOKE_DEFAULT')

    def exit_button(self, widget):
        # print(f'exit {widget.search_index} , {self.active_index}')
        # this condition checks if there wasn't another button already entered, which can happen with small button gaps
        if self.active_index == widget.button_index + self.scroll_offset:
            scene = bpy.context.scene
            ui_props = bpy.context.window_manager.blenderkitUI
            ui_props.draw_tooltip = False
            self.draw_tooltip = False
            self.hide_tooltip()
        # popup asset card on mouse down
        # if utils.experimental_enabled():
        #     h = widget.get_area_height()
        #     print(h,h-self.mouse_y,self.panel.y_screen, self.panel.y,widget.y_screen, widget.y)
        # if utils.experimental_enabled() and self.mouse_y<widget.y_screen:
        #     self.active_index = widget.button_index + self.scroll_offset
        # bpy.ops.wm.blenderkit_asset_popup('INVOKE_DEFAULT')

    def drag_drop_asset(self, widget):
        bpy.ops.view3d.asset_drag_drop('INVOKE_DEFAULT', asset_search_index=widget.search_index + self.scroll_offset)

    def cancel_press(self, widget):
        self.finish()

    def asset_menu(self, widget):
        self.hide_tooltip()
        bpy.ops.wm.blenderkit_asset_popup('INVOKE_DEFAULT')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_asset_menu')

    def search_more(self):
        sro = bpy.context.window_manager.get('search results orig')
        if sro is None:
            return
        if sro.get('next') is None:
            return
        search_props = utils.get_search_props()
        if search_props.is_searching:
            return

        blenderkit.search.search(get_next=True)

    def update_validation_icon(self, asset_button, asset_data):
        if utils.profile_is_validator():
            ar = bpy.context.window_manager.get('asset ratings')
            rating = ar.get(asset_data['id'])
            if rating is not None:
                rating = rating.to_dict()

            v_icon = ui.verification_icons[asset_data.get('verificationStatus', 'validated')]
            if v_icon is not None:
                img_fp = paths.get_addon_thumbnail_path(v_icon)
                asset_button.validation_icon.set_image(img_fp)
                asset_button.validation_icon.visible = True
            elif rating in (None, {}):
                v_icon = 'star_grey.png'
                img_fp = paths.get_addon_thumbnail_path(v_icon)
                asset_button.validation_icon.set_image(img_fp)
                asset_button.validation_icon.visible = True
            else:
                asset_button.validation_icon.visible = False
        else:
            if asset_data.get('canDownload', True) == 0:
                img_fp = paths.get_addon_thumbnail_path('locked.png')
                asset_button.validation_icon.set_image(img_fp)
            else:
                asset_button.validation_icon.visible = False

    def update_images(self):
        sr = bpy.context.window_manager.get('search results')
        if not sr:
            return
        for asset_button in self.asset_buttons:
            if asset_button.visible:
                asset_button.asset_index = asset_button.button_index + self.scroll_offset
                if asset_button.asset_index < len(sr):

                    asset_data = sr[asset_button.asset_index]

                    iname = blenderkit.utils.previmg_name(asset_button.asset_index)
                    # show indices for debug purposes
                    # asset_button.text = str(asset_button.asset_index)
                    img = bpy.data.images.get(iname)
                    if img is None or len(img.pixels) == 0:
                        img_filepath = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')
                    else:
                        img_filepath = img.filepath
                    # print(asset_button.button_index, img_filepath)

                    asset_button.set_image(img_filepath)
                    self.update_validation_icon(asset_button, asset_data)

                    if utils.profile_is_validator() and asset_data['verificationStatus'] == 'uploaded':
                        over_limit = utils.is_upload_old(asset_data)
                        if over_limit:
                            redness = min(over_limit * .05, 0.7)
                            asset_button.red_alert.bg_color = (1, 0, 0, redness)
                            asset_button.red_alert.visible = True
                        else:
                            asset_button.red_alert.visible = False
                    elif utils.profile_is_validator():
                        asset_button.red_alert.visible = False
                else:
                    asset_button.validation_icon.visible = False
                    if utils.profile_is_validator():
                        asset_button.red_alert.visible = False

    def scroll_update(self):
        sr = bpy.context.window_manager.get('search results')
        sro = bpy.context.window_manager.get('search results orig')
        # empty results
        if sr is None:
            self.button_scroll_down.visible = False
            self.button_scroll_up.visible = False
            return

        self.scroll_offset = min(self.scroll_offset, len(sr) - (self.wcount * self.hcount))
        self.scroll_offset = max(self.scroll_offset, 0)
        self.update_images()
        # print(sro)
        if sro['count'] > len(sr) and len(sr) - self.scroll_offset < (self.wcount * self.hcount) + 15:
            self.search_more()

        if self.scroll_offset == 0:
            self.button_scroll_down.visible = False
        else:
            self.button_scroll_down.visible = True

        if self.scroll_offset >= sro['count'] - (self.wcount * self.hcount):
            self.button_scroll_up.visible = False
        else:
            self.button_scroll_up.visible = True

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
            self.search_by_author(self.active_index)
            return True
        return False

    def scroll_up(self, widget):
        self.scroll_offset += self.wcount * self.hcount
        self.scroll_update()

    def scroll_down(self, widget):
        self.scroll_offset -= self.wcount * self.hcount
        self.scroll_update()


def register():
    bpy.utils.register_class(BlenderKitAssetBarOperator)


def unregister():
    bpy.utils.unregister_class(BlenderKitAssetBarOperator)
