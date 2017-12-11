import bpy
import datetime

from . properties import *
from . operators import *
from . sun_calc import Degrees, format_lat_long, degToRad, \
    format_time, format_hms, Move_sun

#---------------------------------------------------------------------------
#
#   Draw the Sun Panel, sliders, et. al.
#
#---------------------------------------------------------------------------


class SunPos_Panel(bpy.types.Panel):

    bl_idname = "panel.SunPos_world"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Sun Position"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.area.type == 'PROPERTIES':
            return 1
        return 0

    def enable(self, layout):
        row = layout.row()
        split = row.split(percentage=.90)
        colL = split.column()
        colL.alignment = 'LEFT'
        colR = split.column()
        colR.alignment = 'RIGHT'
        colL.operator('world.sunpos_controller', 'Enable', icon='PLAY')
        colR.operator('world.sunpos_preferences', '', icon='PREFERENCES')
        Map.init_zoom_preference = True

    def disable(self, context, layout):
        p = context.scene.SunPos_pref_property
        if Map.init_zoom_preference:
            Map.zoom_preferences(bpy.context.user_preferences.inputs.invert_zoom_wheel,
                                 bpy.context.user_preferences.inputs.invert_mouse_zoom)
            Hdr.zoom_preferences(bpy.context.user_preferences.inputs.invert_zoom_wheel,
                                 bpy.context.user_preferences.inputs.invert_mouse_zoom)
        row = self.layout.row()
        if p.UseOneColumn:
            col1 = row.column()
            col2 = col1
        elif p.UseTimePlace:
            split = row.split(percentage=.3)
            col1 = split.column()
            col2 = split.column()
        else:
            col1 = row.column()

        col1.operator('world.sunpos_controller', 'Disable', icon='X')
        if p.UseTimePlace:
            col2.operator_menu_enum('world.pdp_operator',
                                    'timePlacePresets', text=Sun.PlaceLabel)

    def show_preferences(self, context, layout):
        p = context.scene.SunPos_pref_property
        box = self.layout.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Preferences")
        col = box.column(align=True)
        col.label(text="Usage mode:")
        col.props_enum(p, "UsageMode")
        col.separator()

        if p.UsageMode == "NORMAL":
            cb = col.box()
            tr = cb.row()
            rr = tr.row(align=True)
            cs = rr.split()
            cl = cs.column()
            cr = cs.column()

            cl.label(text="World map options:")
            cl.operator_menu_enum('world.wmp_operator',
                                  'mapPresets', text=Sun.MapName)
            cr.label(text="Display map in:")
            cr.props_enum(p, "MapLocation")
            col.separator()
            col.label(text="Show or use:")
            col.alignment = 'LEFT'
            col.prop(p, "UseOneColumn", text="Single column mode")
            col.prop(p, "UseTimePlace", text="Time/place presets")
            col.prop(p, "UseObjectGroup", text="Object group")
            col.prop(p, "ShowDMS", text="D\xb0 M' S\"")
            col.prop(p, "ShowNorth", text="North offset")
            col.prop(p, "ShowRefraction", text="Refraction")
            col.prop(p, "ShowAzEl", text="Azimuth, elevation")
            col.prop(p, "ShowDST", text="Daylight savings time")
            col.prop(p, "ShowRiseSet", text="Sunrise, sunset")
            col.separator()
        col.operator('world.sunpos_pref_done', 'Done', icon='QUIT')
        Sun.ShowRiseSet = p.ShowRiseSet

    def draw(self, context):
        sp = context.scene.SunPos_property
        p = context.scene.SunPos_pref_property
        layout = self.layout
        if Display.PREFERENCES:
            self.show_preferences(context, layout)
        elif Display.ENABLE:
            Sun.SP = sp
            Sun.PP = p
            self.enable(layout)
        else:
            Sun.SP = sp
            Sun.PP = p
            self.disable(context, layout)
        if Display.PANEL:
            if Sun.SP.IsActive:
                self.draw_panel(context, sp, p, layout)
            else:
                Display.setAction('ENABLE')

    def draw_panel(self, context, sp, p, layout):
        if p.UsageMode == "HDR":
            self.draw_environ_panel(context, sp, p, layout)
        elif p.UseOneColumn:
            self.draw_one_column(context, sp, p, layout)
        else:
            self.draw_two_columns(context, sp, p, layout)

    def draw_environ_panel(self, context, sp, p, layout):
        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=False)
        row.alignment = 'CENTER'
        col = row.column(align=True)
        have_texture = False

        try:
            col.separator()
            col.label(text="Use environment texture:")
            col.prop_search(sp, "HDR_texture",
                            context.scene.world.node_tree, "nodes", text="")
            col.separator()
            try:
                nt = bpy.context.scene.world.node_tree.nodes
                envTex = nt.get(sp.HDR_texture)
                if envTex:
                    if envTex.type == "TEX_ENVIRONMENT":
                        if envTex.image != None:
                            have_texture = True
                    if Sun.Bind.azDiff == 0:
                        if envTex.texture_mapping.rotation.z == 0.0:
                            Sun.Bind.azDiff = degToRad(90.0)
            except:
                pass
        except:
            pass
        try:
            col.label(text="Use sun object:")
            col.prop_search(sp, "SunObject",
                            context.scene, "objects", text="")
            Sun.SunObject = sp.SunObject
        except:
            pass

        col.separator()
        col.prop(sp, "SunDistance")
        if not sp.BindToSun:
            col.prop(sp, "HDR_elevation")
        col.prop(sp, "HDR_azimuth")
        col.separator()
        toprow1 = box.row()
        row1 = toprow1.row(align=False)
        row1.alignment = 'CENTER'
        if not sp.BindToSun:
            row1.prop(sp, "BindToSun", toggle=True, icon="CONSTRAINT",
                      text="Bind Texture to Sun ")
        else:
            row1.prop(sp, "BindToSun", toggle=True, icon="CONSTRAINT",
                      text="Release binding")

        toprow2 = box.row()
        row2 = toprow2.row(align=False)
        row2.alignment = 'CENTER'
        row2.prop(sp, "ShowHdr", text="Sync Sun to Texture", toggle=True, icon='LAMP_SUN')
        if have_texture == False:
            row2.enabled = False
        elif sp.BindToSun:
            row2.enabled = False
        else:
            row2.enabled = True
        if have_texture == False:
            row1.enabled = False
        elif sp.ShowHdr:
            row1.enabled = False
        else:
            row1.enabled = True

    def draw_one_column(self, context, sp, p, layout):
        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=False)
        row.alignment = 'CENTER'

        col = row.column(align=True)
        col.prop(sp, "UseSkyTexture", text="Cycles sky")
        if sp.UseSkyTexture:
            try:
                col.prop_search(sp, "SkyTexture",
                                context.scene.world.node_tree, "nodes", text="")
            except:
                pass
        col.prop(sp, "UseSunObject", text="Use object")
        if(sp.UseSunObject):
            try:
                col.prop_search(sp, "SunObject",
                                context.scene, "objects", text="")
            except:
                pass

        if p.UseObjectGroup:
            col.prop(sp, "UseObjectGroup", text="Object group")
            if sp.UseObjectGroup:
                Sun.verify_ObjectGroup()
                if len(Sun.Selected_objects) > 0:
                    col.operator('world.sunpos_clear_objects',
                                 'Release Group')
                    col.separator()
                    if(sp.ObjectGroup == 'ECLIPTIC'):
                        col.prop(sp, "TimeSpread")
                    col.props_enum(sp, "ObjectGroup")
                else:
                    col.operator('world.sunpos_set_objects',
                                 'Set Object Group')
            else:
                Sun.ObjectGroup_verified = False

        row = layout.row()
        row.prop(sp, "ShowMap", text="Show Map", toggle=True, icon='WORLD')

        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=True)
        row.alignment = 'CENTER'
        col = row.column(align=True)
        col.alignment = 'CENTER'
        col.prop(sp, "Latitude")
        if p.ShowDMS:
            col.label(text=format_lat_long(sp.Latitude, True))
        col.prop(sp, "Longitude")
        if p.ShowDMS:
            col.label(text=format_lat_long(sp.Longitude, False))
        cb = col.box()
        tr = cb.row()
        rr = tr.row(align=True)
        if p.ShowNorth:
            cs = rr.split()
            cl = cs.column()
            cr = cs.column()
            cl.prop(sp, "ShowNorth", text="Show North", toggle=True)
            cr.prop(sp, "NorthOffset")
            col.prop(sp, "SunDistance")
        else:
            rr.prop(sp, "SunDistance")

        if p.ShowRefraction:
            col.prop(sp, "ShowRefraction", text="Show refraction")
        if p.ShowAzEl:
            col.label(text="Azimuth: " +
                      str(round(Sun.Azimuth, 3)) + Degrees)
            col.label(text="Elevation: " +
                      str(round(Sun.Elevation, 3)) + Degrees)
        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=False)
        row.alignment = 'CENTER'
        col = row.column(align=False)
        col.alignment = 'CENTER'
        tr = col.row()
        rr = tr.row(align=True)

        if Sun.UseDayMonth:
            cs = rr.split(percentage=.82)
            cl = cs.column()
            cl.alignment = 'LEFT'
            cr = cs.column()
            cr.alignment = 'RIGHT'
            cl.prop(sp, "Month")
            cr.operator('world.sunpos_day_range', '',
                        icon='SORTTIME')
            col.prop(sp, "Day")
        else:
            cs = rr.split(percentage=.90)
            cl = cs.column()
            cr = cs.column()
            cl.alignment = 'LEFT'
            cr.alignment = 'RIGHT'
            cl.prop(sp, "Day_of_year")
            cr.operator('world.sunpos_day_range', '',
                        icon='SORTTIME')

        col.prop(sp, "Year")
        col.prop(sp, "UTCzone", slider=True)
        col.prop(sp, "Time")
        lt, ut = format_time(sp.Time, sp.UTCzone,
                             sp.DaylightSavings, sp.Longitude)
        col.label(text=lt, icon='TIME')
        col.label(text="  " + ut, icon='PREVIEW_RANGE')

        if p.ShowRiseSet:
            if Sun.Sunrise.time == Sun.Sunset.time or \
                    Sun.Sunrise.elevation > -0.4 or Sun.Sunset.elevation > -0.4:
                Sun.RiseSetOK = False
                tsr = "Sunrise: --------"
                tss = " Sunset: --------"
            else:
                Sun.RiseSetOK = True
                sr = format_hms(Sun.Sunrise.time)
                ss = format_hms(Sun.Sunset.time)
                tsr = "Sunrise: " + sr
                tss = " Sunset: " + ss
            col.label(text=tsr, icon='LAMP_SUN')
            col.label(text=tss, icon='SOLO_ON')

        if p.ShowDST:
            col.prop(sp, "DaylightSavings", text="Daylight Savings")

    def draw_two_columns(self, context, sp, p, layout):
        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=True)
        row.alignment = 'CENTER'
        col = row.column(align=True)
        split = col.split(percentage=.5)
        cL = split.column()
        cR = split.column()
        cL.alignment = 'LEFT'
        cR.alignment = 'RIGHT'

        cLi = cRi = 1
        cL.prop(sp, "UseSkyTexture", text="Cycles sky")
        if sp.UseSkyTexture:
            try:
                cL.prop_search(sp, "SkyTexture",
                               context.scene.world.node_tree, "nodes", text="")
                cLi += 1
            except:
                pass
        cR.prop(sp, "UseSunObject", text="Use object")
        if(sp.UseSunObject):
            try:
                cR.prop_search(sp, "SunObject",
                               context.scene, "objects", text="")
                cRi += 1
            except:
                pass

        if p.UseObjectGroup:
            cLi += 1
            cL.prop(sp, "UseObjectGroup", text="Object group")
            if sp.UseObjectGroup:
                Sun.verify_ObjectGroup()
                if len(Sun.Selected_objects) > 0:
                    while cRi < cLi:
                        cR.label(text=" ")
                        cRi += 1
                    cL.operator('world.sunpos_clear_objects',
                                'Release Group')
                    cL.label(text=" ")
                    if(sp.ObjectGroup == 'ECLIPTIC'):
                        cR.prop(sp, "TimeSpread")
                    cR.props_enum(sp, "ObjectGroup")
                else:
                    cL.operator('world.sunpos_set_objects',
                                'Set Object Group')
            else:
                Sun.ObjectGroup_verified = False

        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=False)
        row.alignment = 'CENTER'
        col = row.column(align=False)
        col.prop(sp, "ShowMap", text="Show Map", toggle=True, icon='WORLD')
        distanceSet = False

        if p.ShowDMS:
            split = col.split(percentage=.5)
            cL = split.column()
            cR = split.column()
            cL.alignment = 'LEFT'
            cR.alignment = 'RIGHT'

            cL.prop(sp, "Latitude")
            cR.label(text=format_lat_long(sp.Latitude, True))
            cL.prop(sp, "Longitude")
            cR.label(text=format_lat_long(sp.Longitude, False))
            if p.ShowNorth:
                cL.prop(sp, "ShowNorth", text="Show North", toggle=True)
                cR.prop(sp, "NorthOffset")
            if p.ShowAzEl:
                cL.label(text="Azimuth: " +
                         str(round(Sun.Azimuth, 3)) + Degrees)
                cR.label(text="Elevation: " +
                         str(round(Sun.Elevation, 3)) + Degrees)
            if p.ShowRefraction:
                cL.prop(sp, "ShowRefraction", text="Show refraction")
                cR.prop(sp, "SunDistance")
                distanceSet = True
        else:
            cb = col.box()
            tr = cb.row()
            rr = tr.row(align=True)
            cs = rr.split()
            cL = cs.column(align=True)
            cR = cs.column(align=True)
            cL.prop(sp, "Latitude")
            cR.prop(sp, "Longitude")
            if p.ShowNorth:
                col.separator()
                cL.prop(sp, "ShowNorth", text="Show North", toggle=True)
                cR.prop(sp, "NorthOffset")
            if p.ShowAzEl:
                cL.label(text="Azimuth: " +
                         str(round(Sun.Azimuth, 3)) + Degrees)
                cR.label(text="Elevation: " +
                         str(round(Sun.Elevation, 3)) + Degrees)
            if p.ShowRefraction:
                cL.prop(sp, "ShowRefraction", text="Show refraction")
                cR.prop(sp, "SunDistance")
                distanceSet = True
        if not distanceSet:
            col.prop(sp, "SunDistance")

        box = self.layout.box()
        toprow = box.row()
        row = toprow.row(align=False)
        row.alignment = 'CENTER'
        if Sun.UseDayMonth:
            split = row.split(percentage=.5)
            colL = split.column()
            colMid = split.column()
            colMsplit = colMid.split(percentage=.82)
            colM = colMsplit.column()
            colR = colMsplit.column()
            colL.prop(sp, "Month")
            colM.prop(sp, "Day")
            colR.operator('world.sunpos_day_range', '',
                          icon='SORTTIME')
        else:
            split = row.split(percentage=.50)
            colL = split.column()
            colL.alignment = 'LEFT'
            colMid = split.column()
            colMsplit = colMid.split(percentage=.90)
            colM = colMsplit.column()
            colR = colM.column()
            colR.alignment = 'RIGHT'
            colL.prop(sp, "Day_of_year")
            colR.operator('world.sunpos_day_range', '',
                          icon='SORTTIME')

        colL.prop(sp, "Year")
        colM.prop(sp, "UTCzone", slider=True)
        lt, ut = format_time(sp.Time,
                             sp.UTCzone,
                             sp.DaylightSavings,
                             sp.Longitude)
        colL.prop(sp, "Time")
        colM.label(text=lt, icon='TIME')
        if p.ShowDST:
            colL.prop(sp, "DaylightSavings", text="Daylight Savings")
        colM.label(text="  " + ut, icon='PREVIEW_RANGE')
        if p.ShowRiseSet:
            if Sun.Sunrise.time == Sun.Sunset.time or \
                    Sun.Sunrise.elevation > -0.4 or Sun.Sunset.elevation > -0.4:
                Sun.RiseSetOK = False
                tsr = "Sunrise: --------"
                tss = " Sunset: --------"
            else:
                Sun.RiseSetOK = True
                sr = format_hms(Sun.Sunrise.time)
                ss = format_hms(Sun.Sunset.time)
                tsr = "Sunrise: " + sr
                tss = " Sunset: " + ss
            colL.label(text=tsr, icon='LAMP_SUN')
            if p.ShowDST:
                colM.label(text=tss, icon='SOLO_ON')
            else:
                colL.label(text=tss, icon='SOLO_ON')

############################################################################


class SunPos_OT_Preferences(bpy.types.Operator):
    bl_idname = "world.sunpos_preferences"
    bl_label = "Set preferences"
    bl_description = "Press to set your preferences"

    def execute(self, context):
        Display.setAction('PREFERENCES')
        return {'FINISHED'}


class SunPos_OT_PreferencesDone(bpy.types.Operator):
    bl_idname = "world.sunpos_pref_done"
    bl_label = "Preferences done"
    bl_description = "Press to complete your preferences"

    def execute(self, context):
        Display.setAction('ENABLE')
        p = context.scene.SunPos_pref_property
        Sun.UsageMode = p.UsageMode
        Sun.MapLocation = p.MapLocation
        if not p.UseObjectGroup:
            sp = context.scene.SunPos_property
            sp.UseObjectGroup = False
            Sun.UseObjectGroup = False
        return {'FINISHED'}


class SunPos_OT_DayRange(bpy.types.Operator):
    bl_idname = "world.sunpos_day_range"
    bl_label = "toggleDayRange"
    bl_description = "Toggle day or (month / day) range"

    def execute(self, context):
        sp = context.scene.SunPos_property

        if Sun.UseDayMonth:
            try:
                dt = datetime.date(sp.Year, sp.Month, sp.Day)
                sp.Day_of_year = dt.timetuple().tm_yday
            except:
                pass
            Sun.UseDayMonth = False
        else:
            Sun.UseDayMonth = True
            dt = (datetime.date(sp.Year, 1, 1) +
                  datetime.timedelta(sp.Day_of_year - 1))
            sp.Day = dt.day
            sp.Month = dt.month
        return {'FINISHED'}


class SunPos_OT_SetObjectGroup(bpy.types.Operator):
    bl_idname = "world.sunpos_set_objects"
    bl_label = "Set object group"
    bl_description = "Set currently selected objects as object group"

    def execute(self, context):
        del Sun.Selected_objects[:]
        del Sun.Selected_names[:]
        if (len(bpy.context.selected_objects) > 0):
            Sun.Selected_names = [x.name for x in bpy.context.selected_objects]
            Sun.Selected_objects = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            Move_sun()
        else:
            self.report({'WARNING'}, "No objects selected")
        return {'FINISHED'}


class SunPos_OT_ClearObjectGroup(bpy.types.Operator):
    bl_idname = "world.sunpos_clear_objects"
    bl_label = "Release object group"
    bl_description = "Release object group"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        Sun.ObjectGroup_verified = False
        Sun.verify_ObjectGroup()
        try:
            for x in Sun.Selected_objects:
                x.select = True
        except:
            pass
        del Sun.Selected_objects[:]
        del Sun.Selected_names[:]
        return {'FINISHED'}

# ---------------------------------------------------------------------------
# Choice List of places, month and day at 12:00 noon
# ---------------------------------------------------------------------------


class SunPos_OT_TimePlace(bpy.types.Operator):
    bl_idname = "world.pdp_operator"
    bl_label = "Place & Day Presets"

    #-----------  Description  --------- M   D UTC    Lat      Long   DaySav
    pdp = [["North Pole, Summer Solstice", 6, 21, 0, 90.000, 0.0000, False],
           ["Equator, Vernal Equinox", 3, 20, 0, 0.0000, 0.0000, False],
           ["Rio de Janeiro, May 10th", 5, 10, 3, -22.9002, -43.2334, False],
           ["Tokyo, August 20th", 8, 20, 9, 35.7002, 139.7669, False],
           ["Boston, Autumnal Equinox", 9, 22, 5, 42.3502, -71.0500, True],
           ["Boston, Vernal Equinox", 3, 20, 5, 42.3502, -71.0500, True],
           ["Honolulu, Winter Solstice", 12, 21, 10, 21.3001, -157.850, False],
           ["Honolulu, Summer Solstice", 6, 21, 10, 21.3001, -157.850, False]]

    from bpy.props import EnumProperty

    timePlacePresets = EnumProperty(
        name="Time & place presets",
        description="Preset Place & Day",
        items=(
            ("7", pdp[7][0], ""),
            ("6", pdp[6][0], ""),
            ("5", pdp[5][0], ""),
            ("4", pdp[4][0], ""),
            ("3", pdp[3][0], ""),
            ("2", pdp[2][0], ""),
            ("1", pdp[1][0], ""),
            ("0", pdp[0][0], ""),
        ),
        default="4")

    def execute(self, context):
        sp = context.scene.SunPos_property
        pdp = self.pdp
        i = int(self.properties.timePlacePresets)
        it = pdp[i]
        Sun.PlaceLabel = it[0]
        sp.Month = it[1]
        sp.Day = it[2]
        sp.Time = 12.00
        sp.UTCzone = it[3]
        sp.Latitude = it[4]
        sp.Longitude = it[5]
        sp.DaylightSavings = it[6]
        dt = datetime.date(sp.Year, sp.Month, sp.Day)
        sp.Day_of_year = dt.timetuple().tm_yday
        # Force screen update
        Display.refresh()

        return {'FINISHED'}

# ---------------------------------------------------------------------------
# Choice List of world maps
# ---------------------------------------------------------------------------


class SunPos_OT_MapChoice(bpy.types.Operator):
    bl_idname = "world.wmp_operator"
    bl_label = "World map files"
    """
    wmp = [["1536 x 768", "WorldMap.jpg"],
           ["768 x 384", "WorldMapLR.jpg"],
           ["512 x 256", "WorldMapLLR.jpg"],
           ["Textureless", "None"]]
    """
    # S.L. provide one single optimized map < 100k
    wmp = [["1536 x 768", "World.jpg"],
           ["Textureless", "None"]]
    from bpy.props import EnumProperty

    mapPresets = EnumProperty(
        name="World map presets",
        description="world map files",
        items=(
            # ("3", wmp[3][0], ""),
            #("2", wmp[2][0], ""),
            ("1", wmp[1][0], ""),
            ("0", wmp[0][0], ""),
        ),
        default="1")

    def execute(self, context):
        sp = context.scene.SunPos_property
        wmp = self.wmp
        i = int(self.properties.mapPresets)
        sp.MapName = wmp[i]
        Sun.MapName = wmp[i][1]

        return {'FINISHED'}
