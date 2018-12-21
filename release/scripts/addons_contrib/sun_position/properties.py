import bpy
from bpy.props import (
    StringProperty, EnumProperty,
    IntProperty, FloatProperty,
    BoolProperty
)
from bpy.types import (
    PropertyGroup
)

class DisplayAction:
    ENABLE = True
    PANEL = False
    PREFERENCES = False

    def __init__(self):
        self.invert_zoom_wheel = False
        self.invert_mouse_zoom = False

    def setAction(self, VAL):
        if VAL == 'ENABLE':
            self.ENABLE = True
            self.PANEL = self.PREFERENCES = False
        elif VAL == 'PANEL':
            self.PANEL = True
            self.ENABLE = self.PREFERENCES = False
        else:
            self.PREFERENCES = True
            self.ENABLE = self.PANEL = False

    def refresh(self):
        # Touching the cursor forces a screen refresh
        bpy.context.scene.cursor_location.x += 0.0


Display = DisplayAction()
Display.setAction('ENABLE')

############################################################################
# SunClass is used for storing and comparing changes in panel values
# as well as general traffic direction.
############################################################################


class SunClass:

    class TazEl:
        time = 0.0
        azimuth = 0.0
        elevation = 0.0

    class CLAMP:
        tex_location = None
        elevation = 0.0
        azimuth = 0.0
        azStart = 0.0
        azDiff = 0.0

    Sunrise = TazEl()
    Sunset = TazEl()
    SolarNoon = TazEl()
    RiseSetOK = False

    Bind = CLAMP()
    BindToSun = False
    PlaceLabel = "Time & Place"
    PanelLabel = "Panel Location"
    MapName = "World.jpg"
    MapLocation = 'VIEWPORT'

    Latitude = 0.0
    Longitude = 0.0
    Elevation = 0.0
    Azimuth = 0.0
    AzNorth = 0.0
    Phi = 0.0
    Theta = 0.0
    LX = 0.0
    LY = 0.0
    LZ = 0.0

    Month = 0
    Day = 0
    Year = 0
    Day_of_year = 0
    Time = 0.0

    UTCzone = 0
    SunDistance = 0.0
    TimeSpread = 23.50
    UseDayMonth = True
    DaylightSavings = False
    ShowRiseSet = True
    ShowRefraction = True
    NorthOffset = 0.0

    UseSunObject = False
    SunObject = "Sun"

    UseSkyTexture = False
    SkyTexture = "Sky Texture"
    HDR_texture = "Environment Texture"

    UseObjectGroup = False
    ObjectGroup = 'ECLIPTIC'
    Selected_objects = []
    Selected_names = []
    ObjectGroup_verified = False

    PreBlend_handler = None
    Frame_handler = None
    SP = None
    PP = None
    Counter = 0

    # ----------------------------------------------------------------------
    # There are times when the object group needs to be deleted such as
    # when opening a new file or when objects might be deleted that are
    # part of the group. If such is the case, delete the object group.
    # ----------------------------------------------------------------------

    def verify_ObjectGroup(self):
        if not self.ObjectGroup_verified:
            if len(self.Selected_names) > 0:
                names = [x.name for x in bpy.data.objects]
                for x in self.Selected_names:
                    if not x in names:
                        del self.Selected_objects[:]
                        del self.Selected_names[:]
                        break
            self.ObjectGroup_verified = True

Sun = SunClass()

############################################################################
# Sun panel properties
############################################################################


class SunPosSettings(PropertyGroup):

    IsActive = BoolProperty(
        description="True if panel enabled.",
        default=False)

    ShowMap = BoolProperty(
        description="Show world map.",
        default=False)

    DaylightSavings = BoolProperty(
        description="Daylight savings time adds 1 hour to standard time.",
        default=0)

    ShowRefraction = BoolProperty(
        description="Show apparent sun position due to refraction.",
        default=1)

    ShowNorth = BoolProperty(
        description="Draws line pointing north.",
        default=0)

    Latitude = FloatProperty(
        attr="",
        name="Latitude",
        description="Latitude: (+) Northern (-) Southern",
        soft_min=-90.000, soft_max=90.000, step=3.001,
        default=40.000, precision=3)

    Longitude = FloatProperty(
        attr="",
        name="Longitude",
        description="Longitude: (-) West of Greenwich  (+) East of Greenwich",
        soft_min=-180.000, soft_max=180.000,
        step=3.001, default=1.000, precision=3)

    Month = IntProperty(
        attr="",
        name="Month",
        description="",
        min=1, max=12, default=6)

    Day = IntProperty(
        attr="",
        name="Day",
        description="",
        min=1, max=31, default=21)

    Year = IntProperty(
        attr="",
        name="Year",
        description="",
        min=1800, max=4000, default=2012)

    Day_of_year = IntProperty(
        attr="",
        name="Day of year",
        description="",
        min=1, max=366, default=1)

    UTCzone = IntProperty(
        attr="",
        name="UTC zone",
        description="Time zone: Difference from Greenwich England in hours.",
        min=0, max=12, default=0)

    Time = FloatProperty(
        attr="",
        name="Time",
        description="",
        precision=4,
        soft_min=0.00, soft_max=23.9999, step=1.00, default=12.00)

    NorthOffset = FloatProperty(
        attr="",
        name="",
        description="North offset in degrees or radians "
                    "from scene's units settings",
        unit="ROTATION",
        soft_min=-3.14159265, soft_max=3.14159265, step=10.00, default=0.00)

    SunDistance = FloatProperty(
        attr="",
        name="Distance",
        description="Distance to sun from XYZ axes intersection.",
        unit="LENGTH",
        soft_min=1, soft_max=3000.00, step=10.00, default=50.00)

    UseSunObject = BoolProperty(
        description="Enable sun positioning of named lamp or mesh",
        default=False)

    SunObject = StringProperty(
        default="Sun",
        name="theSun",
        description="Name of sun object")

    UseSkyTexture = BoolProperty(
        description="Enable use of Cycles' "
                    "sky texture. World nodes must be enabled, "
                    "then set color to Sky Texture.",
        default=False)

    SkyTexture = StringProperty(
        default="Sky Texture",
        name="sunSky",
        description="Name of sky texture to be used")

    ShowHdr = BoolProperty(
        description="Click to set sun location on environment texture",
        default=False)

    HDR_texture = StringProperty(
        default="Environment Texture",
        name="envSky",
        description="Name of texture to use. World nodes must be enabled "
                    "and color set to Environment Texture")

    HDR_azimuth = FloatProperty(
        attr="",
        name="Rotation",
        description="Rotation angle of sun and environment texture "
                    "in degrees or radians from scene's units settings",
        unit="ROTATION",
        step=1.00, default=0.00, precision=3)

    HDR_elevation = FloatProperty(
        attr="",
        name="Elevation",
        description="Elevation angle of sun",
        step=3.001,
        default=0.000, precision=3)

    BindToSun = BoolProperty(
        description="If true, Environment texture moves with sun.",
        default=False)

    UseObjectGroup = BoolProperty(
        description="Allow a group of objects to be positioned.",
        default=False)

    TimeSpread = FloatProperty(
        attr="",
        name="Time Spread",
        description="Time period in which to spread object group",
        precision=4,
        soft_min=1.00, soft_max=24.00, step=1.00, default=23.00)

    ObjectGroup = EnumProperty(
        name="Display type",
        description="Show object group on ecliptic or as analemma",
        items=(
            ('ECLIPTIC', "On the Ecliptic", ""),
            ('ANALEMMA', "As and Analemma", ""),
        ),
        default='ECLIPTIC')

    Location = StringProperty(
        default="view3d",
        name="location",
        description="panel location")


############################################################################
# Preference panel properties
############################################################################


class SunPosPreferences(PropertyGroup):

    UsageMode = EnumProperty(
        name="Usage mode",
        description="operate in normal mode or environment texture mode",
        items=(
            ('NORMAL', "Normal", ""),
            ('HDR', "Sun + HDR texture", ""),
        ),
        default='NORMAL')

    MapLocation = EnumProperty(
        name="Map location",
        description="Display map in viewport or world panel",
        items=(
            ('VIEWPORT', "Viewport", ""),
            ('PANEL', "Panel", ""),
        ),
        default='VIEWPORT')

    UseOneColumn = BoolProperty(
        description="Set panel to use one column.",
        default=False)

    UseTimePlace = BoolProperty(
        description="Show time/place presets.",
        default=False)

    UseObjectGroup = BoolProperty(
        description="Use object group option.",
        default=True)

    ShowDMS = BoolProperty(
        description="Show lat/long degrees,minutes,seconds labels.",
        default=True)

    ShowNorth = BoolProperty(
        description="Show north offset choice and slider.",
        default=True)

    ShowRefraction = BoolProperty(
        description="Show sun refraction choice.",
        default=True)

    ShowAzEl = BoolProperty(
        description="Show azimuth and solar elevation info.",
        default=True)

    ShowDST = BoolProperty(
        description="Show daylight savings time choice.",
        default=True)

    ShowRiseSet = BoolProperty(
        description="Show sunrise and sunset.",
        default=True)

    MapName = StringProperty(
        default="WorldMap.jpg",
        name="WorldMap",
        description="Name of world map")
