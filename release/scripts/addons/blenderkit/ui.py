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


if "bpy" in locals():
    import importlib

    paths = importlib.reload(paths)
    ratings = importlib.reload(ratings)
    utils = importlib.reload(utils)
    search = importlib.reload(search)
    upload = importlib.reload(upload)
    ui_bgl = importlib.reload(ui_bgl)
    download = importlib.reload(download)
    bg_blender = importlib.reload(bg_blender)
else:
    from blenderkit import paths, ratings, utils, search, upload, ui_bgl, download, bg_blender

import bpy

import math, random

from bpy.props import (
    BoolProperty,
    StringProperty
)

from bpy_extras import view3d_utils
import mathutils
from mathutils import Vector
import time
import os

handler_2d = None
handler_3d = None

mappingdict = {
    'MODEL': 'model',
    'SCENE': 'scene',
    'MATERIAL': 'material',
    'TEXTURE': 'texture',
    'BRUSH': 'brush'
}

verification_icons = {
    'ready': 'vs_ready.png',
    'deleted': 'vs_deleted.png',
    'uploaded': 'vs_uploaded.png',
    'uploading': None,
    'on_hold': 'vs_on_hold.png',
    'validated': None

}


# class UI_region():
#      def _init__(self, parent = None, x = 10,y = 10 , width = 10, height = 10, img = None, col = None):

def get_approximate_text_width(st):
    size = 10
    for s in st:
        if s in 'i|':
            size += 2
        elif s in ' ':
            size += 4
        elif s in 'sfrt':
            size += 5
        elif s in 'ceghkou':
            size += 6
        elif s in 'PadnBCST3E':
            size += 7
        elif s in 'GMODVXYZ':
            size += 8
        elif s in 'w':
            size += 9
        elif s in 'm':
            size += 10
        else:
            size += 7
    return size  # Convert to picas


def get_asset_under_mouse(mousex, mousey):
    s = bpy.context.scene
    ui_props = bpy.context.scene.blenderkitUI
    r = bpy.context.region

    search_results = s.get('search results')
    if search_results is not None:

        h_draw = min(ui_props.hcount, math.ceil(len(search_results) / ui_props.wcount))
        for b in range(0, h_draw):
            w_draw = min(ui_props.wcount, len(search_results) - b * ui_props.wcount - ui_props.scrolloffset)
            for a in range(0, w_draw):
                x = ui_props.bar_x + a * (ui_props.margin + ui_props.thumb_size) + ui_props.margin + ui_props.drawoffset
                y = ui_props.bar_y - ui_props.margin - (ui_props.thumb_size + ui_props.margin) * (b + 1)
                w = ui_props.thumb_size
                h = ui_props.thumb_size

                if x < mousex < x + w and y < mousey < y + h:
                    return a + ui_props.wcount * b + ui_props.scrolloffset

                #   return search_results[a]

    return -3


def draw_bbox(location, rotation, bbox_min, bbox_max, progress=None, color=(0, 1, 0, 1)):
    ui_props = bpy.context.scene.blenderkitUI

    rotation = mathutils.Euler(rotation)

    smin = Vector(bbox_min)
    smax = Vector(bbox_max)
    v0 = Vector(smin)
    v1 = Vector((smax.x, smin.y, smin.z))
    v2 = Vector((smax.x, smax.y, smin.z))
    v3 = Vector((smin.x, smax.y, smin.z))
    v4 = Vector((smin.x, smin.y, smax.z))
    v5 = Vector((smax.x, smin.y, smax.z))
    v6 = Vector((smax.x, smax.y, smax.z))
    v7 = Vector((smin.x, smax.y, smax.z))

    arrowx = smin.x + (smax.x - smin.x) / 2
    arrowy = smin.y - (smax.x - smin.x) / 2
    v8 = Vector((arrowx, arrowy, smin.z))

    vertices = [v0, v1, v2, v3, v4, v5, v6, v7, v8]
    for v in vertices:
        v.rotate(rotation)
        v += Vector(location)

    lines = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5],
             [2, 6], [3, 7], [0, 8], [1, 8]]
    ui_bgl.draw_lines(vertices, lines, color)
    if progress != None:
        color = (color[0], color[1], color[2], .2)
        progress = progress * .01
        vz0 = (v4 - v0) * progress + v0
        vz1 = (v5 - v1) * progress + v1
        vz2 = (v6 - v2) * progress + v2
        vz3 = (v7 - v3) * progress + v3
        rects = (
            (v0, v1, vz1, vz0),
            (v1, v2, vz2, vz1),
            (v2, v3, vz3, vz2),
            (v3, v0, vz0, vz3))
        for r in rects:
            ui_bgl.draw_rect_3d(r, color)


def get_rating_scalevalues(asset_type):
    xs = []
    if asset_type == 'model':
        scalevalues = (0.5, 1, 2, 5, 10, 25, 50, 100, 250)
        for v in scalevalues:
            a = math.log2(v)
            x = (a + 1) * (1. / 9.)
            xs.append(x)
    else:
        scalevalues = (0.2, 1, 2, 3, 4, 5)
        for v in scalevalues:
            a = v
            x = v / 5.
            xs.append(x)
    return scalevalues, xs


def draw_ratings_bgl():
    # return;
    ui = bpy.context.scene.blenderkitUI

    rating_possible, rated, asset, asset_data = is_rating_possible()

    if rating_possible:  # (not rated or ui_props.rating_menu_on):
        bkit_ratings = asset.bkit_ratings
        bgcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner
        textcol = (1, 1, 1, 1)

        r = bpy.context.region
        font_size = int(ui.rating_ui_scale * 20)

        if ui.rating_button_on:
            img = utils.get_thumbnail('star_white.png')

            ui_bgl.draw_image(ui.rating_x,
                              ui.rating_y - ui.rating_button_width,
                              ui.rating_button_width,
                              ui.rating_button_width,
                              img, 1)

            # if ui_props.asset_type != 'BRUSH':
            #     thumbnail_image = props.thumbnail
            # else:
            #     b = utils.get_active_brush()
            #     thumbnail_image = b.icon_filepath

            directory = paths.get_temp_dir('%s_search' % asset_data['asset_type'])
            tpath = os.path.join(directory, asset_data['thumbnail_small'])

            img = utils.get_hidden_image(tpath, 'rating_preview')
            ui_bgl.draw_image(ui.rating_x + ui.rating_button_width,
                              ui.rating_y - ui.rating_button_width,
                              ui.rating_button_width,
                              ui.rating_button_width,
                              img, 1)
            # ui_bgl.draw_text( 'rate asset %s' % asset_data['name'],r.width - rating_button_width + margin, margin, font_size)
            return

        ui_bgl.draw_rect(ui.rating_x,
                         ui.rating_y - ui.rating_ui_height - 2 * ui.margin - font_size,
                         ui.rating_ui_width + ui.margin,
                         ui.rating_ui_height + 2 * ui.margin + font_size,
                         bgcol)
        img = utils.get_thumbnail('rating_ui.png')
        ui_bgl.draw_image(ui.rating_x,
                          ui.rating_y - ui.rating_ui_height - 2 * ui.margin,
                          ui.rating_ui_width,
                          ui.rating_ui_height,
                          img, 1)
        img = utils.get_thumbnail('star_white.png')

        quality = bkit_ratings.rating_quality
        work_hours = bkit_ratings.rating_work_hours

        for a in range(0, quality):
            ui_bgl.draw_image(ui.rating_x + ui.quality_stars_x + a * ui.star_size,
                              ui.rating_y - ui.rating_ui_height + ui.quality_stars_y,
                              ui.star_size,
                              ui.star_size,
                              img, 1)

        img = utils.get_thumbnail('bar_slider.png')
        # for a in range(0,11):
        if work_hours > 0.2:
            if asset_data['asset_type'] == 'model':
                complexity = math.log2(work_hours) + 2  # real complexity
                complexity = (1. / 9.) * (complexity - 1) * ui.workhours_bar_x_max
            else:
                complexity = work_hours / 5 * ui.workhours_bar_x_max
            ui_bgl.draw_image(
                ui.rating_x + ui.workhours_bar_x + int(
                    complexity),
                ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y,
                ui.workhours_bar_slider_size,
                ui.workhours_bar_slider_size, img, 1)
            ui_bgl.draw_text(
                str(round(work_hours, 1)),
                ui.rating_x + ui.workhours_bar_x - 50,
                ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y + 10, font_size)
        # (0.5,1,2,4,8,16,32,64,128,256)
        # ratings have to be different for models and brushes+materials.

        scalevalues, xs = get_rating_scalevalues(asset_data['asset_type'])
        for v, x in zip(scalevalues, xs):
            ui_bgl.draw_rect(ui.rating_x + ui.workhours_bar_x + int(
                x * ui.workhours_bar_x_max) - 1 + ui.workhours_bar_slider_size / 2,
                             ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y,
                             2,
                             5,
                             textcol)
            ui_bgl.draw_text(str(v),
                             ui.rating_x + ui.workhours_bar_x + int(
                                 x * ui.workhours_bar_x_max),
                             ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y - 30,
                             font_size)
        if work_hours > 0.2 and quality > 0.2:
            text = 'Thanks for rating asset %s' % asset_data['name']
        else:
            text = 'Rate asset %s.' % asset_data['name']
        ui_bgl.draw_text(text,
                         ui.rating_x,
                         ui.rating_y - ui.margin - font_size,
                         font_size)


def draw_tooltip(x, y, text='', author='', img=None):
    region = bpy.context.region
    scale = bpy.context.preferences.view.ui_scale
    t = time.time()

    ttipmargin = 10

    font_height = int(12 * scale)
    line_height = int(15 * scale)
    nameline_height = int(23 * scale)

    lines = text.split('\n')
    ncolumns = 2
    nlines = math.ceil((len(lines) - 1) / ncolumns)
    texth = line_height * nlines + nameline_height

    isizex = int(512 * scale * img.size[0] / max(img.size[0], img.size[1]))
    isizey = int(512 * scale * img.size[1] / max(img.size[0], img.size[1]))

    estimated_height = 3 * ttipmargin + isizey

    if estimated_height > y:
        scaledown = y / (estimated_height)
        scale *= scaledown
        # we need to scale these down to have correct size if the tooltip wouldn't fit.
        font_height = int(12 * scale)
        line_height = int(15 * scale)
        nameline_height = int(23 * scale)

        lines = text.split('\n')
        ncolumns = 2
        nlines = math.ceil((len(lines) - 1) / ncolumns)
        texth = line_height * nlines + nameline_height

        isizex = int(512 * scale * img.size[0] / max(img.size[0], img.size[1]))
        isizey = int(512 * scale * img.size[1] / max(img.size[0], img.size[1]))

    name_height = int(18 * scale)

    x += 2 * ttipmargin
    y -= 2 * ttipmargin

    width = isizex + 2 * ttipmargin

    properties_width = 0
    for r in bpy.context.area.regions:
        if r.type == 'UI':
            properties_width = r.width

    x = min(x + width, region.width - properties_width) - width

    bgcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner
    bgcol1 = (bgcol[0], bgcol[1], bgcol[2], .6)
    textcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.text
    textcol = (textcol[0], textcol[1], textcol[2], 1)
    textcol_mild = (textcol[0] * .8, textcol[1] * .8, textcol[2] * .8, 1)
    textcol_strong = (textcol[0] * 1.3, textcol[1] * 1.3, textcol[2] * 1.3, 1)
    white = (1, 1, 1, .1)

    ui_bgl.draw_rect(x - ttipmargin,
                     y - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2,
                     2 * ttipmargin + isizey,
                     bgcol)
    ui_bgl.draw_image(x, y - isizey - ttipmargin, isizex, isizey, img, 1)

    ui_bgl.draw_rect(x - ttipmargin,
                     y - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2,
                     2 * ttipmargin + texth,
                     bgcol1)
    i = 0
    column_break = -1  # start minus one for the name
    xtext = x + ttipmargin
    fsize = name_height
    tcol = textcol
    for l in lines:
        if column_break >= nlines:
            xtext += int(isizex / ncolumns)
            column_break = 0
        ytext = y - column_break * line_height - nameline_height - ttipmargin * 2 - isizey + texth
        if i == 0:
            ytext = y - name_height + 5 - isizey + texth - ttipmargin
        elif i == len(lines) - 1:
            ytext = y - (nlines - 1) * line_height - nameline_height - ttipmargin * 2 - isizey + texth
            tcol = textcol
            tsize = font_height
        else:
            if l[:4] == 'Tip:':
                tcol = textcol_strong
            fsize = font_height
        i += 1
        column_break += 1
        ui_bgl.draw_text(l, xtext, ytext, fsize, tcol)
    t = time.time()


def draw_tooltip_old(x, y, text='', author='', img=None):
    region = bpy.context.region
    scale = bpy.context.preferences.view.ui_scale
    t = time.time()

    ttipmargin = 10

    font_height = int(12 * scale)
    line_height = int(15 * scale)
    nameline_height = int(23 * scale)

    lines = text.split('\n')
    ncolumns = 2
    nlines = math.ceil((len(lines) - 1) / ncolumns)
    texth = line_height * nlines + nameline_height

    isizex = int(512 * scale * img.size[0] / max(img.size[0], img.size[1]))
    isizey = int(512 * scale * img.size[1] / max(img.size[0], img.size[1]))

    estimated_height = texth + 3 * ttipmargin + isizey

    if estimated_height > y:
        scaledown = y / (estimated_height)
        scale *= scaledown
        # we need to scale these down to have correct size if the tooltip wouldn't fit.
        font_height = int(12 * scale)
        line_height = int(15 * scale)
        nameline_height = int(23 * scale)

        lines = text.split('\n')
        ncolumns = 2
        nlines = math.ceil((len(lines) - 1) / ncolumns)
        texth = line_height * nlines + nameline_height

        isizex = int(512 * scale * img.size[0] / max(img.size[0], img.size[1]))
        isizey = int(512 * scale * img.size[1] / max(img.size[0], img.size[1]))

    name_height = int(18 * scale)

    x += 2 * ttipmargin
    y -= 2 * ttipmargin

    width = isizex + 2 * ttipmargin

    properties_width = 0
    for r in bpy.context.area.regions:
        if r.type == 'UI':
            properties_width = r.width

    x = min(x + width, region.width - properties_width) - width

    bgcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner
    textcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.text
    textcol = (textcol[0], textcol[1], textcol[2], 1)
    textcol1 = (textcol[0] * .8, textcol[1] * .8, textcol[2] * .8, 1)
    white = (1, 1, 1, .1)

    ui_bgl.draw_rect(x - ttipmargin,
                     y - texth - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2,
                     texth + 3 * ttipmargin + isizey,
                     bgcol)

    i = 0
    column_break = -1  # start minus one for the name
    xtext = x
    fsize = name_height
    tcol = textcol
    for l in lines:
        if column_break >= nlines:
            xtext += int(isizex / ncolumns)
            column_break = 0
        ytext = y - column_break * line_height - nameline_height - ttipmargin
        if i == 0:
            ytext = y - name_height + 5
        elif i == len(lines) - 1:
            ytext = y - (nlines - 1) * line_height - nameline_height - ttipmargin
            tcol = textcol
            tsize = font_height
        else:
            if l[:5] == 'tags:':
                tcol = textcol1
            fsize = font_height
        i += 1
        column_break += 1
        ui_bgl.draw_text(l, xtext, ytext, fsize, tcol)
    t = time.time()
    ui_bgl.draw_image(x, y - texth - isizey - ttipmargin, isizex, isizey, img, 1)


def draw_callback_2d(self, context):
    a = context.area
    try:
        # self.area might throw error just by itself.
        a1 = self.area
        go = True
    except:
        # bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
        # bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        go = False
    if go and a == a1:
        props = context.scene.blenderkitUI
        if props.down_up == 'SEARCH':
            draw_ratings_bgl()
            draw_callback_2d_search(self, context)
        elif props.down_up == 'UPLOAD':
            draw_callback_2d_upload_preview(self, context)


def draw_downloader(x, y, percent=0, img=None):
    if img is not None:
        ui_bgl.draw_image(x, y, 50, 50, img, .5)
    ui_bgl.draw_rect(x, y, 50, int(0.5 * percent), (.2, 1, .2, .3))
    ui_bgl.draw_rect(x - 3, y - 3, 6, 6, (1, 0, 0, .3))


def draw_progress(x, y, text='', percent=None, color=(.2, 1, .2, .3)):
    ui_bgl.draw_rect(x, y, percent, 5, color)
    ui_bgl.draw_text(text, x, y + 8, 10, color)


def draw_callback_3d_progress(self, context):
    # 'star trek' mode gets here, blocked by now ;)
    for threaddata in download.download_threads:
        asset_data = threaddata[1]
        tcom = threaddata[2]
        if tcom.passargs.get('downloaders'):
            for d in tcom.passargs['downloaders']:
                if asset_data['asset_type'] == 'model':
                    draw_bbox(d['location'], d['rotation'], asset_data['bbox_min'], asset_data['bbox_max'],
                              progress=tcom.progress)


def draw_callback_2d_progress(self, context):
    green = (.2, 1, .2, .3)
    offset = 0
    row_height = 35

    ui = bpy.context.scene.blenderkitUI

    x = ui.reports_x
    y = ui.reports_y
    index = 0
    for threaddata in download.download_threads:
        asset_data = threaddata[1]
        tcom = threaddata[2]
        if tcom.passargs.get('downloaders'):
            for d in tcom.passargs['downloaders']:
                directory = paths.get_temp_dir('%s_search' % asset_data['asset_type'])
                tpath = os.path.join(directory, asset_data['thumbnail_small'])
                img = utils.get_hidden_image(tpath, 'rating_preview')
                loc = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d,
                                                            d['location'])
                if loc is not None:
                    if asset_data['asset_type'] == 'model':
                        # models now draw with star trek mode, no need to draw percent for the image.
                        draw_downloader(loc[0], loc[1], percent=tcom.progress, img=img)
                    else:
                        draw_downloader(loc[0], loc[1], percent=tcom.progress, img=img)


        else:
            draw_progress(x, y - index * 30, text='downloading %s' % asset_data['name'],
                          percent=tcom.progress)
            index += 1
    for process in bg_blender.bg_processes:
        tcom = process[1]
        draw_progress(x, y - index * 30, '%s' % tcom.lasttext,
                      tcom.progress)
        index += 1


def draw_callback_2d_upload_preview(self, context):
    ui_props = context.scene.blenderkitUI

    props = utils.get_upload_props()
    if props != None and ui_props.draw_tooltip:
        if ui_props.asset_type != 'BRUSH':
            ui_props.thumbnail_image = props.thumbnail
        else:
            b = utils.get_active_brush()
            ui_props.thumbnail_image = b.icon_filepath

        img = utils.get_hidden_image(ui_props.thumbnail_image, 'upload_preview')

        draw_tooltip(ui_props.bar_x, ui_props.bar_y, text=ui_props.tooltip, img=img)


def draw_callback_2d_search(self, context):
    s = bpy.context.scene
    ui_props = context.scene.blenderkitUI
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    r = self.region
    # hc = bpy.context.preferences.themes[0].view_3d.space.header
    # hc = bpy.context.preferences.themes[0].user_interface.wcol_menu_back.inner
    # hc = (hc[0], hc[1], hc[2], .2)
    hc = (1, 1, 1, .07)
    # grey1 = (hc.r * .55, hc.g * .55, hc.b * .55, 1)
    grey2 = (hc[0] * .8, hc[1] * .8, hc[2] * .8, .5)
    # grey1 = (hc.r, hc.g, hc.b, 1)
    white = (1, 1, 1, 0.2)
    green = (.2, 1, .2, .7)
    highlight = bpy.context.preferences.themes[0].user_interface.wcol_menu_item.inner_sel
    highlight = (1, 1, 1, .2)
    # highlight = (1, 1, 1, 0.8)
    # background of asset bar
    if not ui_props.dragging:
        search_results = s.get('search results')
        search_results_orig = s.get('search results orig')
        if search_results == None:
            return
        h_draw = min(ui_props.hcount, math.ceil(len(search_results) / ui_props.wcount))

        if ui_props.wcount > len(search_results):
            bar_width = len(search_results) * (ui_props.thumb_size + ui_props.margin) + ui_props.margin
        else:
            bar_width = ui_props.bar_width
        row_height = ui_props.thumb_size + ui_props.margin
        ui_bgl.draw_rect(ui_props.bar_x, ui_props.bar_y - ui_props.bar_height, bar_width,
                         ui_props.bar_height, hc)

        if search_results is not None:
            if ui_props.scrolloffset > 0 or ui_props.wcount * ui_props.hcount < len(search_results):
                ui_props.drawoffset = 35
            else:
                ui_props.drawoffset = 0

            if ui_props.wcount * ui_props.hcount < len(search_results):
                # arrows
                arrow_y = ui_props.bar_y - int((ui_props.bar_height + ui_props.thumb_size) / 2) + ui_props.margin
                if ui_props.scrolloffset > 0:

                    if ui_props.active_index == -2:
                        ui_bgl.draw_rect(ui_props.bar_x, ui_props.bar_y - ui_props.bar_height, 25,
                                         ui_props.bar_height, highlight)
                    img = utils.get_thumbnail('arrow_left.png')
                    ui_bgl.draw_image(ui_props.bar_x, arrow_y, 25,
                                      ui_props.thumb_size,
                                      img,
                                      1)
                if search_results_orig['count'] - ui_props.scrolloffset > (ui_props.wcount * ui_props.hcount):
                    if ui_props.active_index == -1:
                        ui_bgl.draw_rect(ui_props.bar_x + ui_props.bar_width - 25,
                                         ui_props.bar_y - ui_props.bar_height, 25,
                                         ui_props.bar_height,
                                         highlight)
                    img1 = utils.get_thumbnail('arrow_right.png')
                    ui_bgl.draw_image(ui_props.bar_x + ui_props.bar_width - 25,
                                      arrow_y, 25,
                                      ui_props.thumb_size, img1, 1)

            for b in range(0, h_draw):
                w_draw = min(ui_props.wcount, len(search_results) - b * ui_props.wcount - ui_props.scrolloffset)
                y = ui_props.bar_y - (b + 1) * (row_height)
                for a in range(0, w_draw):
                    x = ui_props.bar_x + a * (
                            ui_props.margin + ui_props.thumb_size) + ui_props.margin + ui_props.drawoffset

                    #
                    index = a + ui_props.scrolloffset + b * ui_props.wcount
                    iname = utils.previmg_name(index)
                    img = bpy.data.images.get(iname)

                    w = int(ui_props.thumb_size * img.size[0] / max(img.size[0], img.size[1]))
                    h = int(ui_props.thumb_size * img.size[1] / max(img.size[0], img.size[1]))
                    crop = (0, 0, 1, 1)
                    if img.size[0] > img.size[1]:
                        offset = (1 - img.size[1] / img.size[0]) / 2
                        crop = (offset, 0, 1 - offset, 1)
                    if img is not None:
                        ui_bgl.draw_image(x, y, w, w, img, 1,
                                          crop=crop)
                        if index == ui_props.active_index:
                            ui_bgl.draw_rect(x - ui_props.highlight_margin, y - ui_props.highlight_margin,
                                             w + 2 * ui_props.highlight_margin, w + 2 * ui_props.highlight_margin,
                                             highlight)
                        # if index == ui_props.active_index:
                        #     ui_bgl.draw_rect(x - highlight_margin, y - highlight_margin,
                        #               w + 2*highlight_margin, h + 2*highlight_margin , highlight)

                    else:
                        ui_bgl.draw_rect(x, y, w, h, white)

                    result = search_results[index]
                    if result['downloaded'] > 0:
                        ui_bgl.draw_rect(x, y - 2, int(w * result['downloaded'] / 100.0), 2, green)
                    # object type icons - just a test..., adds clutter/ not so userfull:
                    # icons = ('type_finished.png', 'type_template.png', 'type_particle_system.png')

                    if (result.get('can_download', True)) == 0:
                        img = utils.get_thumbnail('locked.png')
                        ui_bgl.draw_image(x + 2, y + 2, 24, 24, img, 1)

                    v_icon = verification_icons[result.get('verification_status', 'validated')]
                    if v_icon is not None:
                        img = utils.get_thumbnail(v_icon)
                        ui_bgl.draw_image(x + ui_props.thumb_size - 26, y + 2, 24, 24, img, 1)

            if user_preferences.api_key == '':
                report = 'Register on BlenderKit website to upload your own assets.'
                ui_bgl.draw_text(report, ui_props.bar_x + ui_props.margin,
                                 ui_props.bar_y - 25 - ui_props.margin - ui_props.bar_height, 15)
            elif len(search_results) == 0:
                report = 'BlenderKit - No matching results found.'
                ui_bgl.draw_text(report, ui_props.bar_x + ui_props.margin,
                                 ui_props.bar_y - 25 - ui_props.margin, 15)
        s = bpy.context.scene
        props = utils.get_search_props()
        if props.report != '' and props.is_searching or props.search_error:
            ui_bgl.draw_text(props.report, ui_props.bar_x,
                             ui_props.bar_y - 15 - ui_props.margin - ui_props.bar_height, 15)

        props = s.blenderkitUI
        if props.draw_tooltip:
            # TODO move this lazy loading into a function and don't duplicate through the code
            iname = utils.previmg_name(ui_props.active_index, fullsize=True)

            directory = paths.get_temp_dir('%s_search' % mappingdict[props.asset_type])
            sr = s.get('search results')
            if sr != None and ui_props.active_index != -3:
                r = sr[ui_props.active_index]
                tpath = os.path.join(directory, r['thumbnail'])

                img = bpy.data.images.get(iname)
                if img == None or img.filepath != tpath:
                    if os.path.exists(tpath):  # sometimes we are unlucky...

                        if img is None:
                            img = bpy.data.images.load(tpath)
                            img.name = iname
                        else:
                            if img.filepath != tpath:
                                # todo replace imgs reloads with a method that forces unpack for thumbs.
                                if img.packed_file is not None:
                                    img.unpack(method='USE_ORIGINAL')
                                img.filepath = tpath
                                img.reload()
                                img.name = iname
                    else:
                        iname = utils.previmg_name(ui_props.active_index)
                        img = bpy.data.images.get(iname)
                    img.colorspace_settings.name = 'Linear'
                draw_tooltip(ui_props.mouse_x, ui_props.mouse_y, text=ui_props.tooltip, img=img)

    if ui_props.dragging and (
            ui_props.draw_drag_image or ui_props.draw_snapped_bounds) and ui_props.active_index > -1:
        iname = utils.previmg_name(ui_props.active_index)
        img = bpy.data.images.get(iname)
        linelength = 35
        ui_bgl.draw_image(ui_props.mouse_x + linelength, ui_props.mouse_y - linelength - ui_props.thumb_size,
                          ui_props.thumb_size, ui_props.thumb_size, img, 1)
        ui_bgl.draw_line2d(ui_props.mouse_x, ui_props.mouse_y, ui_props.mouse_x + linelength,
                           ui_props.mouse_y - linelength, 2, white)


def draw_callback_3d(self, context):
    ''' Draw snapped bbox while dragging and in the future other blenderkit related stuff. '''
    ui = context.scene.blenderkitUI

    if ui.dragging and ui.asset_type == 'MODEL':
        if ui.draw_snapped_bounds:
            draw_bbox(ui.snapped_location, ui.snapped_rotation, ui.snapped_bbox_min, ui.snapped_bbox_max)


def mouse_raycast(context, mx, my):
    r = context.region
    rv3d = context.region_data
    coord = mx, my

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord)
    ray_target = ray_origin + (view_vector * 1000000000)

    vec = ray_target - ray_origin

    has_hit, snapped_location, snapped_normal, face_index, object, matrix = bpy.context.scene.ray_cast(
        bpy.context.view_layer, ray_origin, vec)

    # rote = mathutils.Euler((0, 0, math.pi))
    randoffset = math.pi
    if has_hit:
        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
        up = Vector((0, 0, 1))
        props = bpy.context.scene.blenderkit_models
        if props.randomize_rotation and snapped_normal.angle(up) < math.radians(10.0):
            randoffset = props.offset_rotation_amount + math.pi + (
                    random.random() - 0.5) * props.randomize_rotation_amount
        else:
            randoffset = props.offset_rotation_amount  # we don't rotate this way on walls and ceilings. + math.pi
        # snapped_rotation.z += math.pi + (random.random() - 0.5) * .2

    else:
        snapped_rotation = mathutils.Quaternion((0, 0, 0, 0)).to_euler()

    snapped_rotation.rotate_axis('Z', randoffset)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, object, matrix


def floor_raycast(context, mx, my):
    r = context.region
    rv3d = context.region_data
    coord = mx, my

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord)
    ray_target = ray_origin + (view_vector * 1000)

    # various intersection plane normals are needed for corner cases that might actually happen quite often - in front and side view.
    # default plane normal is scene floor.
    plane_normal = (0, 0, 1)
    if math.isclose(view_vector.x, 0, abs_tol=1e-4) and math.isclose(view_vector.z, 0, abs_tol=1e-4):
        plane_normal = (0, 1, 0)
    elif math.isclose(view_vector.z, 0, abs_tol=1e-4):
        plane_normal = (1, 0, 0)

    snapped_location = mathutils.geometry.intersect_line_plane(ray_origin, ray_target, (0, 0, 0), plane_normal,
                                                               False)
    if snapped_location != None:
        has_hit = True
        snapped_normal = Vector((0, 0, 1))
        face_index = None
        object = None
        matrix = None
        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
        props = bpy.context.scene.blenderkit_models
        if props.randomize_rotation:
            randoffset = props.offset_rotation_amount + math.pi + (
                    random.random() - 0.5) * props.randomize_rotation_amount
        else:
            randoffset = props.offset_rotation_amount + math.pi
        snapped_rotation.rotate_axis('Z', randoffset)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, object, matrix


def is_rating_possible():
    ao = bpy.context.active_object
    ui = bpy.context.scene.blenderkitUI
    if bpy.context.scene.get('assets rated') is not None and ui.down_up == 'SEARCH':
        if bpy.context.mode in ('SCULPT', 'PAINT_TEXTURE'):
            b = utils.get_active_brush()
            ad = b.get('asset_data')
            if ad is not None:
                rated = bpy.context.scene['assets rated'].get(ad['asset_base_id'])
                return True, rated, b, ad
        if ao is not None:
            # TODO ADD BRUSHES HERE
            ad = ao.get('asset_data')
            if ad is not None:
                rated = bpy.context.scene['assets rated'].get(ad['asset_base_id'])
                # originally hidden for allready rated assets
                return True, rated, ao, ad

            # check also materials
            m = ao.active_material
            if m is not None:
                ad = m.get('asset_data')
                if ad is not None:
                    rated = bpy.context.scene['assets rated'].get(ad['asset_base_id'])
                    return True, rated, m, ad

        # if t>2 and t<2.5:
        #     ui_props.rating_on = False

    return False, False, None, None


def interact_rating(r, mx, my, event):
    ui = bpy.context.scene.blenderkitUI
    rating_possible, rated, asset, asset_data = is_rating_possible()

    if rating_possible:
        bkit_ratings = asset.bkit_ratings

        t = time.time() - ui.last_rating_time
        # if t>2:
        #     if rated:
        #         ui_props.rating_button_on = True
        #         ui_props.rating_menu_on = False
        if ui.rating_button_on and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if mouse_in_area(mx, my,
                             ui.rating_x,
                             ui.rating_y - ui.rating_button_width,
                             ui.rating_button_width * 2,
                             ui.rating_button_width):
                ui.rating_menu_on = True
                ui.rating_button_on = False
                return True
        if ui.rating_menu_on:
            if mouse_in_area(mx, my,
                             ui.rating_x,
                             ui.rating_y - ui.rating_ui_height,
                             ui.rating_ui_width,
                             ui.rating_ui_height + 25):
                rmx = mx - (ui.rating_x)
                rmy = my - (ui.rating_y - ui.rating_ui_height)

                # quality
                upload_rating = False
                if (ui.quality_stars_x < rmx and rmx < ui.quality_stars_x + 10 * ui.star_size and \
                    ui.quality_stars_y < rmy and rmy < ui.quality_stars_y + ui.star_size and event.type == 'LEFTMOUSE' and event.value == 'PRESS') or \
                        ui.dragging_rating_quality:

                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            ui.dragging_rating = True
                            ui.dragging_rating_quality = True
                        elif event.value == 'RELEASE':
                            ui.dragging_rating = False
                            ui.dragging_rating_quality = False

                    if ui.dragging_rating_quality:
                        q = math.ceil((rmx - ui.quality_stars_x) / (float(ui.star_size)))
                        bkit_ratings.rating_quality = q

                # work hours
                if (
                        ui.workhours_bar_x < rmx and rmx < ui.workhours_bar_x + ui.workhours_bar_x_max + ui.workhours_bar_slider_size and \
                        ui.workhours_bar_y < rmy and rmy < ui.workhours_bar_y + ui.workhours_bar_slider_size and event.type == 'LEFTMOUSE' and event.value == 'PRESS') \
                        or (ui.dragging_rating_work_hours):
                    if event.value == 'PRESS':
                        ui.dragging_rating = True
                        ui.dragging_rating_work_hours = True
                    elif event.value == 'RELEASE':
                        ui.dragging_rating = False
                        ui.dragging_rating_work_hours = False
                    if ui.dragging_rating_work_hours:
                        xv = rmx - ui.workhours_bar_x - ui.workhours_bar_slider_size / 2
                        ratio = xv / ui.workhours_bar_x_max
                        if asset_data['asset_type'] == 'model':
                            wh_log2 = ratio * 9 - 1
                            wh = 2 ** wh_log2
                        else:
                            wh = 5 * ratio
                        bkit_ratings.rating_work_hours = wh

                if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                    if bkit_ratings.rating_quality > 0.1 or bkit_ratings.rating_work_hours > 0.1:
                        ratings.upload_rating(asset)
                    ui.last_rating_time = time.time()
                return True
            else:
                ui.rating_button_on = True
                ui.rating_menu_on = False
    return False


def mouse_in_area(mx, my, x, y, w, h):
    if x < mx < x + w and y < my < y + h:
        return True
    else:
        return False


def mouse_in_asset_bar(mx, my):
    ui_props = bpy.context.scene.blenderkitUI
    if ui_props.bar_y - ui_props.bar_height < my < ui_props.bar_y \
            and mx > ui_props.bar_x and mx < ui_props.bar_x + ui_props.bar_width:
        return True
    else:
        return False


def mouse_in_region(r, mx, my):
    if 0 < my < r.height and 0 < mx < r.width:
        return True
    else:
        return False


def update_ui_size(area, region):
    ui = bpy.context.scene.blenderkitUI
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    ui_scale = bpy.context.preferences.view.ui_scale

    ui.margin = ui.bl_rna.properties['margin'].default * ui_scale
    ui.thumb_size = ui.bl_rna.properties['thumb_size'].default * ui_scale

    reg_multiplier = 1
    if not bpy.context.preferences.system.use_region_overlap:
        reg_multiplier = 0

    for r in area.regions:
        if r.type == 'TOOLS':
            ui.bar_x = r.width * reg_multiplier + ui.margin + ui.bar_x_offset * ui_scale
        elif r.type == 'UI':
            ui.bar_end = r.width * reg_multiplier + 100 * ui_scale

    ui.bar_width = region.width - ui.bar_x - ui.bar_end
    ui.wcount = math.floor(
        (ui.bar_width - 2 * ui.drawoffset) / (ui.thumb_size + ui.margin))

    search_results = bpy.context.scene.get('search results')
    if search_results != None:
        ui.hcount = min(user_preferences.max_assetbar_rows, math.ceil(len(search_results) / ui.wcount))
    else:
        ui.hcount = 1
    ui.bar_height = (ui.thumb_size + ui.margin) * ui.hcount + ui.margin
    ui.bar_y = region.height - ui.bar_y_offset * ui_scale
    if ui.down_up == 'UPLOAD':
        ui.reports_y = ui.bar_y + 800
        ui.reports_x = ui.bar_x
    else:
        ui.reports_y = ui.bar_y + ui.bar_height
        ui.reports_x = ui.bar_x

    ui.rating_x = ui.bar_x
    ui.rating_y = ui.bar_y - ui.bar_height


class AssetBarOperator(bpy.types.Operator):
    '''runs search and displays the asset bar at the same time'''
    bl_idname = "view3d.blenderkit_asset_bar"
    bl_label = "BlenderKit Asset Bar UI"
    bl_options = {'REGISTER', 'UNDO'}

    do_search: BoolProperty(name="Run Search", description='', default=True, options={'SKIP_SAVE'})
    keep_running: BoolProperty(name="Keep Running", description='', default=True, options={'SKIP_SAVE'})
    free_only: BoolProperty(name="Free Only", description='', default=False, options={'SKIP_SAVE'})

    category: StringProperty(
        name="Category",
        description="search only subtree of this category",
        default="", options={'SKIP_SAVE'})

    def search_more(self):
        sro = bpy.context.scene.get('search results orig')
        if sro is not None and sro.get('next') is not None:
            search.search(get_next=True)

    def exit_modal(self):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        except:
            pass;
        ui_props = bpy.context.scene.blenderkitUI

        ui_props.dragging = False
        ui_props.tooltip = ''
        ui_props.active_index = -3
        ui_props.draw_drag_image = False
        ui_props.draw_snapped_bounds = False
        ui_props.has_hit = False
        ui_props.assetbar_on = False

    def modal(self, context, event):
        # This is for case of closing the area or changing type:
        ui_props = context.scene.blenderkitUI
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

        areas = []

        for w in context.window_manager.windows:
            areas.extend(w.screen.areas)
        if bpy.context.scene != self.scene:
            self.exit_modal()
            ui_props.assetbar_on = False
            return {'CANCELLED'}

        if self.area not in areas or self.area.type != 'VIEW_3D':
            # print('search areas')
            # stopping here model by now - because of:
            #   switching layouts or maximizing area now fails to assign new area throwing the bug
            #   internal error: modal gizmo-map handler has invalid area
            self.exit_modal()
            ui_props.assetbar_on = False
            return {'CANCELLED'}

            newarea = None
            for a in context.window.screen.areas:
                if a.type == 'VIEW_3D':
                    self.area = a
                    for r in a.regions:
                        if r.type == 'WINDOW':
                            self.region = r
                    newarea = a
                    break;
                    # context.area = a

            # we check again and quit if things weren't fixed this way.
            if newarea == None:
                self.exit_modal()
                ui_props.assetbar_on = False
                return {'CANCELLED'}

        update_ui_size(self.area, self.region)

        search.timer_update()
        download.timer_update()
        bg_blender.bg_update()

        if context.region != self.region:
            return {'PASS_THROUGH'}

        # this was here to check if sculpt stroke is running, but obviously that didn't help,
        #  since the RELEASE event is cought by operator and thus there is no way to detect a stroke has ended...
        if bpy.context.mode in ('SCULPT', 'PAINT_TEXTURE'):
            if event.type == 'MOUSEMOVE':  # ASSUME THAT SCULPT OPERATOR ACTUALLY STEALS THESE EVENTS,
                # SO WHEN THERE ARE SOME WE CAN APPEND BRUSH...
                bpy.context.window_manager['appendable'] = True
            if event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    bpy.context.window_manager['appendable'] = False

        self.area.tag_redraw()
        s = context.scene

        if ui_props.turn_off:
            ui_props.assetbar_on = False
            ui_props.turn_off = False
            self.exit_modal()
            ui_props.draw_tooltip = False
            return {'CANCELLED'}

        if ui_props.down_up == 'UPLOAD':

            ui_props.mouse_x = 0
            ui_props.mouse_y = self.region.height

            mx = event.mouse_x
            my = event.mouse_y

            ui_props.draw_tooltip = True

            # only generate tooltip once in a while
            if (
                    event.type == 'LEFTMOUSE' or event.type == 'RIGHTMOUSE') and event.value == 'RELEASE' or event.type == 'ENTER' or ui_props.tooltip == '':
                ao = bpy.context.active_object
                if ui_props.asset_type == 'MODEL' and ao != None \
                        or ui_props.asset_type == 'MATERIAL' and ao != None and ao.active_material != None \
                        or ui_props.asset_type == 'BRUSH':
                    export_data, upload_data, eval_path_computing, eval_path_state, eval_path, props = upload.get_upload_data(
                        self,
                        context,
                        ui_props.asset_type)
                    ui_props.tooltip = search.generate_tooltip(upload_data)

            return {'PASS_THROUGH'}

        # TODO add one more condition here to take less performance.
        r = self.region
        s = bpy.context.scene
        sr = s.get('search results')

        # If there aren't any results, we need no interaction(yet)
        if sr is None:
            return {'PASS_THROUGH'}
        if len(sr) - ui_props.scrolloffset < (ui_props.wcount * ui_props.hcount) + 10:
            self.search_more()
        if event.type == 'WHEELUPMOUSE' or event.type == 'WHEELDOWNMOUSE' or event.type == 'TRACKPADPAN':
            # scrolling
            mx = event.mouse_region_x
            my = event.mouse_region_y

            if ui_props.dragging and not mouse_in_asset_bar(mx, my):  # and my < r.height - ui_props.bar_height \
                # and mx > 0 and mx < r.width and my > 0:
                sprops = bpy.context.scene.blenderkit_models
                if event.type == 'WHEELUPMOUSE':
                    sprops.offset_rotation_amount += sprops.offset_rotation_step
                elif event.type == 'WHEELDOWNMOUSE':
                    sprops.offset_rotation_amount -= sprops.offset_rotation_step

                #### TODO - this snapping code below is 3x in this file.... refactor it.
                ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = mouse_raycast(
                    context, mx, my)

                # MODELS can be dragged on scene floor
                if not ui_props.has_hit and ui_props.asset_type == 'MODEL':
                    ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = floor_raycast(
                        context,
                        mx, my)

                return {'RUNNING_MODAL'}

            if not mouse_in_asset_bar(mx, my):
                return {'PASS_THROUGH'}

            # note - TRACKPADPAN is unsupported in blender by now.
            # if event.type == 'TRACKPADPAN' :
            #     print(dir(event))
            #     print(event.value, event.oskey, event.)
            if (event.type == 'WHEELDOWNMOUSE') and len(sr) - ui_props.scrolloffset > ui_props.wcount:
                ui_props.scrolloffset += 1

            if event.type == 'WHEELUPMOUSE' and ui_props.scrolloffset > 0:
                ui_props.scrolloffset -= 1
            return {'RUNNING_MODAL'}
        if event.type == 'MOUSEMOVE':  # Apply

            r = self.region
            mx = event.mouse_region_x
            my = event.mouse_region_y

            ui_props.mouse_x = mx
            ui_props.mouse_y = my

            if ui_props.dragging_rating or ui_props.rating_menu_on:
                res = interact_rating(r, mx, my, event)
                if res == True:
                    return {'RUNNING_MODAL'}

            if ui_props.drag_init:
                ui_props.drag_length += 1
                if ui_props.drag_length > 0:
                    ui_props.dragging = True
                    ui_props.drag_init = False

            if not (ui_props.dragging and mouse_in_region(r, mx, my)) and not mouse_in_asset_bar(mx, my):
                ui_props.active_index = -3
                ui_props.draw_tooltip = False
                bpy.context.window.cursor_set("DEFAULT")
                return {'PASS_THROUGH'}

            sr = bpy.context.scene['search results']

            if not ui_props.dragging:
                bpy.context.window.cursor_set("DEFAULT")

                if sr != None and ui_props.wcount * ui_props.hcount > len(sr) and ui_props.scrolloffset > 0:
                    ui_props.scrolloffset = 0

                asset_search_index = get_asset_under_mouse(mx, my)
                ui_props.active_index = asset_search_index
                if asset_search_index > -1:

                    asset_data = sr[asset_search_index]
                    ui_props.draw_tooltip = True

                    ui_props.tooltip = asset_data['tooltip']
                else:
                    ui_props.draw_tooltip = False

                if mx > ui_props.bar_x + ui_props.bar_width - 50 and len(sr) - ui_props.scrolloffset > (
                        ui_props.wcount * ui_props.hcount):
                    ui_props.active_index = -1
                    return {'RUNNING_MODAL'}
                if mx < ui_props.bar_x + 50 and ui_props.scrolloffset > 0:
                    ui_props.active_index = -2
                    return {'RUNNING_MODAL'}

            else:
                result = False
                if ui_props.dragging and not mouse_in_asset_bar(mx, my) and mouse_in_region(r, mx, my):
                    ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = mouse_raycast(
                        context, mx, my)
                    # MODELS can be dragged on scene floor
                    if not ui_props.has_hit and ui_props.asset_type == 'MODEL':
                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = floor_raycast(
                            context,
                            mx, my)
                if ui_props.has_hit and ui_props.asset_type == 'MODEL':
                    # this condition is here to fix a bug for a scene submitted by a user, so this situation shouldn't
                    # happen anymore, but there might exists scenes which have this problem for some reason.
                    if ui_props.active_index < len(sr) and ui_props.active_index > -1:
                        ui_props.draw_snapped_bounds = True
                        active_mod = sr[ui_props.active_index]
                        ui_props.snapped_bbox_min = Vector(active_mod['bbox_min'])
                        ui_props.snapped_bbox_max = Vector(active_mod['bbox_max'])

                else:
                    ui_props.draw_snapped_bounds = False
                    ui_props.draw_drag_image = True
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE':

            r = self.region
            mx = event.mouse_x - r.x
            my = event.mouse_y - r.y

            ui_props = context.scene.blenderkitUI
            if event.value == 'PRESS' and ui_props.active_index > -1:
                if ui_props.asset_type == 'MODEL' or ui_props.asset_type == 'MATERIAL':
                    ui_props.drag_init = True
                    bpy.context.window.cursor_set("NONE")
                    ui_props.draw_tooltip = False
                    ui_props.drag_length = 0

            if ui_props.rating_on:
                res = interact_rating(r, mx, my, event)
                if res:
                    return {'RUNNING_MODAL'}

            if not ui_props.dragging and not mouse_in_asset_bar(mx, my):
                return {'PASS_THROUGH'}

            # this can happen by switching result asset types - length of search result changes
            if ui_props.scrolloffset > 0 and (ui_props.wcount * ui_props.hcount) > len(sr) - ui_props.scrolloffset:
                ui_props.scrolloffset = len(sr) - (ui_props.wcount * ui_props.hcount)

            if event.value == 'RELEASE':  # Confirm
                ui_props.drag_init = False

                # scroll by a whole page
                if mx > ui_props.bar_x + ui_props.bar_width - 50 and len(
                        sr) - ui_props.scrolloffset > ui_props.wcount * ui_props.hcount:
                    ui_props.scrolloffset = min(
                        ui_props.scrolloffset + (ui_props.wcount * ui_props.hcount),
                        len(sr) - ui_props.wcount * ui_props.hcount)
                    return {'RUNNING_MODAL'}
                if mx < ui_props.bar_x + 50 and ui_props.scrolloffset > 0:
                    ui_props.scrolloffset = max(0, ui_props.scrolloffset - ui_props.wcount * ui_props.hcount)
                    return {'RUNNING_MODAL'}

                # Drag-drop interaction
                if ui_props.dragging and mouse_in_region(r, mx, my):
                    asset_search_index = ui_props.active_index
                    # raycast here
                    ui_props.active_index = -3

                    if ui_props.asset_type == 'MODEL':

                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = mouse_raycast(
                            context, mx, my)

                        # MODELS can be dragged on scene floor
                        if not ui_props.has_hit and ui_props.asset_type == 'MODEL':
                            ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = floor_raycast(
                                context,
                                mx, my)

                        if not ui_props.has_hit:
                            return {'RUNNING_MODAL'}

                        target_object = ''
                        if object is not None:
                            target_object = object.name
                        target_slot = ''

                    if ui_props.asset_type == 'MATERIAL':
                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = mouse_raycast(
                            context, mx, my)

                        if not ui_props.has_hit:
                            # this is last attempt to get object under mouse - for curves and other objects than mesh.
                            ui_props.dragging = False
                            sel = utils.selection_get()
                            bpy.ops.view3d.select(location=(event.mouse_region_x, event.mouse_region_y))
                            sel1 = utils.selection_get()
                            if sel[0] != sel1[0] and sel1[0].type != 'MESH':
                                object = sel1[0]
                                target_slot = sel1[0].active_material_index
                                ui_props.has_hit = True
                            utils.selection_set(sel)

                        if not ui_props.has_hit:
                            return {'RUNNING_MODAL'}

                        else:
                            # first, test if object can have material applied.
                            if object is not None and not object.is_library_indirect:
                                target_object = object.name
                                # create final mesh to extract correct material slot
                                depsgraph = bpy.context.evaluated_depsgraph_get()
                                object_eval = object.evaluated_get(depsgraph)
                                temp_mesh = object_eval.to_mesh()
                                target_slot = temp_mesh.polygons[face_index].material_index
                                object_eval.to_mesh_clear()
                            else:
                                self.report({'WARNING'}, "Invalid or library object as input:")
                                target_object = ''
                                target_slot = ''

                # Click interaction
                else:
                    asset_search_index = get_asset_under_mouse(mx, my)

                    if ui_props.asset_type in ('MATERIAL',
                                               'MODEL'):  # this was meant for particles, commenting for now or ui_props.asset_type == 'MODEL':
                        ao = bpy.context.active_object
                        if ao != None and not ao.is_library_indirect:
                            target_object = bpy.context.active_object.name
                            target_slot = bpy.context.active_object.active_material_index
                        else:
                            target_object = ''
                            target_slot = ''
                # FIRST START SEARCH

                if asset_search_index == -3:
                    return {'RUNNING_MODAL'}
                if asset_search_index > -3:
                    if ui_props.asset_type == 'MATERIAL':
                        if target_object != '':
                            # position is for downloader:
                            loc = ui_props.snapped_location
                            rotation = (0, 0, 0)

                            asset_data = sr[asset_search_index]
                            utils.automap(target_object, target_slot=target_slot,
                                          tex_size=asset_data.get('texture_size_meters', 1.0))
                            bpy.ops.scene.blenderkit_download(True,
                                                              asset_type=ui_props.asset_type,
                                                              asset_index=asset_search_index,
                                                              model_location=loc,
                                                              model_rotation=rotation,
                                                              target_object=target_object,
                                                              material_target_slot=target_slot)


                    elif ui_props.asset_type == 'MODEL':
                        if ui_props.has_hit and ui_props.dragging:
                            loc = ui_props.snapped_location
                            rotation = ui_props.snapped_rotation
                        else:
                            loc = s.cursor.location
                            rotation = s.cursor.rotation_euler

                        bpy.ops.scene.blenderkit_download(True,
                                                          asset_type=ui_props.asset_type,
                                                          asset_index=asset_search_index,
                                                          model_location=loc,
                                                          model_rotation=rotation,
                                                          target_object=target_object)

                    else:
                        bpy.ops.scene.blenderkit_download(asset_type=ui_props.asset_type,
                                                          asset_index=asset_search_index)

                    ui_props.dragging = False
                    return {'RUNNING_MODAL'}
            else:
                return {'RUNNING_MODAL'}

        if event.type == 'W' and ui_props.active_index != -3:
            sr = bpy.context.scene['search results']
            asset_data = sr[ui_props.active_index]
            a = bpy.context.window_manager['bkit authors'].get(asset_data['author_id'])
            if a is not None:
                utils.p('author:', a)
                if a.get('aboutMeUrl') is not None:
                    bpy.ops.wm.url_open(url=a['aboutMeUrl'])
            return {'RUNNING_MODAL'}
        if event.type == 'A' and ui_props.active_index != -3:
            sr = bpy.context.scene['search results']
            asset_data = sr[ui_props.active_index]
            a = asset_data['author_id']
            if a is not None:
                utils.p('author:', a)
                search.search(author_id=a)
            return {'RUNNING_MODAL'}
        if event.type == 'X' and ui_props.active_index != -3:
            sr = bpy.context.scene['search results']
            asset_data = sr[ui_props.active_index]
            print(asset_data['name'])
            print('delete')
            paths.delete_asset_debug(asset_data)
            asset_data['downloaded'] = 0
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        # FIRST START SEARCH
        ui_props = context.scene.blenderkitUI

        if self.do_search:
            # we erase search keywords for cateogry search now, since these combinations usually return nothing now.
            # when the db gets bigger, this can be deleted.
            if self.category != '':
                sprops = utils.get_search_props()
                sprops.search_keywords = ''
            search.search(category=self.category)

        if ui_props.assetbar_on:
            # we don't want to run the assetbar many times, that's why it has a switch on/off behaviour,
            # unless being called with 'keep_running' prop.
            if not self.keep_running:
                # this sends message to the originally running operator, so it quits, and then it ends this one too.
                # If it initiated a search, the search will finish in a thread. The switch off procedure is run
                # by the 'original' operator, since if we get here, it means
                # same operator is allready running.
                ui_props.turn_off = True
                # if there was an error, we need to turn off these props so we can restart after 2 clicks
                ui_props.assetbar_on = False

            else:
                pass
            return {'FINISHED'}

        ui_props.dragging = False  # only for cases where assetbar ended with an error.
        ui_props.assetbar_on = True
        ui_props.turn_off = False

        sr = bpy.context.scene.get('search results')
        if sr is None:
            bpy.context.scene['search results'] = []

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            self.area = context.area
            self.scene = bpy.context.scene

            for r in self.area.regions:
                if r.type == 'WINDOW':
                    self.region = r

            update_ui_size(self.area, self.region)

            self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
            self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, 'WINDOW', 'POST_VIEW')

            context.window_manager.modal_handler_add(self)
            ui_props.assetbar_on = True
            return {'RUNNING_MODAL'}
        else:

            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def execute(self, context):
        return {'RUNNING_MODAL'}


classess = (
    AssetBarOperator,

)

# store keymaps here to access after registration
addon_keymaps = []


def register_ui():
    global handler_2d, handler_3d

    for c in classess:
        bpy.utils.register_class(c)

    args = (None, bpy.context)

    handler_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d_progress, args, 'WINDOW', 'POST_PIXEL')
    handler_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d_progress, args, 'WINDOW', 'POST_VIEW')

    wm = bpy.context.window_manager

    # spaces solved by registering shortcut to Window. Couldn't register object mode before somehow.
    if not wm.keyconfigs.addon:
        return
    km = wm.keyconfigs.addon.keymaps.new(name="Window", space_type='EMPTY')
    kmi = km.keymap_items.new(AssetBarOperator.bl_idname, 'SEMI_COLON', 'PRESS', ctrl=False, shift=False)
    kmi.properties.keep_running = False
    kmi.properties.do_search = False

    addon_keymaps.append(km)


def unregister_ui():
    global handler_2d, handler_3d

    bpy.types.SpaceView3D.draw_handler_remove(handler_2d, 'WINDOW')
    bpy.types.SpaceView3D.draw_handler_remove(handler_3d, 'WINDOW')

    for c in classess:
        bpy.utils.unregister_class(c)

    args = (None, bpy.context)

    wm = bpy.context.window_manager
    if not wm.keyconfigs.addon:
        return

    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    del addon_keymaps[:]
