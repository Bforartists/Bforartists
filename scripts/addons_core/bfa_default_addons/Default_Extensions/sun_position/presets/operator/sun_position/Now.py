import bpy
from datetime import datetime

TODAY = datetime.today()
sun_props = bpy.context.scene.sun_pos_properties
sun_props.day = TODAY.day
sun_props.month = TODAY.month
sun_props.year = TODAY.year
sun_props.time = TODAY.hour + TODAY.minute / 60.0 + TODAY.second / 3600.0
