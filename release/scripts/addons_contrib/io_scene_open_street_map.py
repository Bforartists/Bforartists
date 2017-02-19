# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

# <pep8 compliant>

bl_info = {
    "name": "Open Street Map (.osm)",
    "author": "Michael Anthrax Schlachter, ideasman42, littleneo",
    "version": (0, 2),
    "blender": (2, 63, 0),
    "location": "File > Import",
    "description": "Load Open Street Map File",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export"}

# originally written for blender 2.4x by (manthrax _at_ hotmail.com),
# updated for blender 2.6x by ideasman42
# If you use it for something cool, send me an email and let me know!

import bpy
from mathutils import Vector, Matrix
import math
from math import radians, sin, cos, tan, sqrt

# add more osm tags here.
# http://wiki.openstreetmap.org/wiki/Map_Features
osmkeys = [
    'highway',
    'barrier',
    'wall',
    'cycleway',
    'bicycle',
    'waterway',
    'railway',
    'aeroway',
    'aerialway',
    'power',
    'man_made',
    'building',
    'leisure',
    'amenity',
    'office',
    'shop',
    'craft',
    'emergency',
    'tourism',
    'historic',
    'landuse',
    'military',
    'natural',
]

# just a try for nodes, for retrieving v tag values.
# keyname must exists in osmkeys
osmvals = {'highway': ['traffic_signals']}

# vertex group name -> vertex group index lookup
grouplookup = {}


def parseBranch(nodes, bm, nmap, obj, scale=100.0, tag=False, UTM=False):
    vgroups = bm.verts.layers.deform.verify()
    tidx = 0
    inNode = 0
    dlong = clat = clong = minlat = maxlat = minlong = maxlong = 0.0
    dlat = 1.0  # avoid divide by zero

    for node in nodes:
        if node.localName == "bounds":
            if node.hasAttributes():
                for i in range(node.attributes.length):
                    at = node.attributes.item(i)
                    if at.name == "minlat":
                        minlat = float(at.nodeValue)
                    elif at.name == "minlon":
                        minlong = float(at.nodeValue)
                    elif at.name == "maxlat":
                        maxlat = float(at.nodeValue)
                    elif at.name == "maxlon":
                        maxlong = float(at.nodeValue)
                dlat = maxlat - minlat
                dlong = maxlong - minlong
                clat = (maxlat + minlat) * 0.5
                clong = (maxlong + minlong) * 0.5

                if UTM:
                    dlong, dlat = geoToUTM(dlong, dlat)
                    clong, clat = geoToUTM(clong, clat)

                print(dlat, dlong, clat, clong)

        if node.localName == "way":
            wayid = node.getAttribute('id')
            nid = None
            refs = []
            if tag:
                group = obj.vertex_groups.new('way_%s' % wayid)
                gid = len(obj.vertex_groups) - 1
            '''
            if node.hasAttributes():
                for i in range(node.attributes.length):
                    at=node.attributes.item(i)
                    print(at.name)
            '''

            if tag:
                metagid = []
                for ch in node.childNodes:
                    if ch.localName == "tag":
                        key = ch.getAttribute('k')
                        if key in osmkeys:
                            metagid.append(grouplookup[key])

            for ch in node.childNodes:
                if ch.localName == "nd":
                    for i in range(ch.attributes.length):
                        at = ch.attributes.item(i)
                        if at.name == "ref":
                            vid = int(at.nodeValue)
                            refs.append(vid)
                            if tag:
                                vert = nmap[vid]
                                weigths = vert[vgroups]
                                weigths[gid] = 1.0
                                for mid in metagid:
                                    weigths[mid] = 1.0

            first = True
            for r in refs:
                if first is False:
                    edge = bm.edges.get((nmap[pr], nmap[r]))
                    if edge is None:
                        edge = bm.edges.new((nmap[pr], nmap[r]))
                    del edge  # don't actually use it
                else:
                    first = False
                pr = r

        if node.localName == "node":
            if node.hasAttributes():
                nid = node.getAttribute('id')
                nlong = node.getAttribute('lon')
                nlat = node.getAttribute('lat')

                # is this test necessary ? maybe for faulty .osm files
                if (nid != '') and (nlat != '') and (nlong != ''):

                    if UTM:
                        nlong, nlat = geoToUTM(float(nlong), float(nlat))
                    else:
                        nlat = float(nlat)
                        nlong = float(nlong)

                    x = (nlong - clong) * scale / dlat
                    y = (nlat - clat) * scale / dlat
                    vert = bm.verts.new((x, y, 0.0))
                    nmap[int(nid)] = vert
                    if tag:
                        metagid = []
                        for ch in node.childNodes:
                            if ch.localName == "tag":
                                key = ch.getAttribute('k')
                                val = ch.getAttribute('v')
                                if key in osmvals and val in osmvals[key]:
                                    metagid.append(grouplookup[key])
                                    metagid.append(grouplookup['_V_' + val])
                                    weigths = vert[vgroups]
                                    group = obj.vertex_groups.new('node_%s' % nid)
                                    gid = len(obj.vertex_groups) - 1
                                    weigths[gid] = 1.0
                                    for mid in metagid:
                                        weigths[mid] = 1.0
                else:
                    print('node is missing some elements : %s %s %s' % (nid, nlat, nlong))

        tidx += 1
        # if tidx > 1000:
        #     break
        tidx += parseBranch(node.childNodes, bm, nmap, obj, scale, tag, UTM)

    return tidx


def read(context, filepath, scale=100.0, tag=False, utm=False):
    import bmesh
    from xml.dom import minidom

    # create mesh
    bm = bmesh.new()
    name = bpy.path.display_name_from_filepath(filepath)
    me = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, me)

    # osm tags option
    if tag:
        tvid = 0
        for gid, grname in enumerate(osmkeys):
            obj.vertex_groups.new('_' + grname)
            grouplookup[grname] = gid + tvid
            if grname in osmvals:
                for val in osmvals[grname]:
                    tvid += 1
                    obj.vertex_groups.new('_V_' + val)
                    grouplookup['_V_' + val] = gid + tvid

    # get xml then feed bmesh
    print("Reading xml...")
    xmldoc = minidom.parse(filepath)

    print("Starting parse: %r..." % filepath)
    nmap = {}
    tidx = parseBranch(xmldoc.childNodes, bm, nmap, obj, scale, tag, utm)

    bm.to_mesh(me)

    # fast approximation of utm for not too big area
    if utm is False:
        global_matrix = Matrix(((0.65, 0.0, 0.0, 0.0),
                                (0.0, 1.0, 0.0, 0.0),
                                (0.0, 0.0, 1.0, 0.0),
                                (0.0, 0.0, 0.0, 1.0)))
        me.transform(global_matrix)

    # create the object in the scene
    scene = context.scene
    scene.objects.link(obj)
    scene.objects.active = obj
    obj.select = True

    # entry points for other addons
    obj['osmfile'] = filepath
    obj['tagged'] = tag
    obj['utm'] = utm

    print("Parse done... %d" % tidx)

    return {'FINISHED'}


# given lat and longitude in degrees, returns x and y in UTM kilometers.
# accuracy : supposed to be centimeter :)
# http://fr.wikipedia.org/wiki/Projection_UTM
# http://fr.wikipedia.org/wiki/WGS_84
# http://earth-info.nga.mil/GandG/publications/tr8350.2/wgs84fin.pdf
# http://geodesie.ign.fr/contenu/fichiers/documentation/algorithmes/alg0071.pdf
def geoToUTM(lon, lat):

    # if abs(lat) > 80 : lat = 80 #wrong coords.

    # UTM zone, longitude origin, then lat lon in radians
    z = int((lon + 180) / 6) + 1
    lon0 = radians(6 * z - 183)
    lat = radians(lat)
    lon = radians(lon)

    # CONSTANTS (see refs.)
    # rayon de la terre à l'équateur
    a = 6378.137
    K0 = 0.9996
    # flattening consts
    f  = 0.0033528106647474805   # 1 / 298.257223563
    e2 = 0.0066943799901413165   # 2*f - f**2
    e4 = 4.481472345240445e-05   # e2**2
    e6 = 3.0000678794349315e-07  # e2**3

    # lat0. 10000 for South, 0 for North
    N0 = 10000 if lat < 0 else 0

    # wiki is your friend (don't ask me Im just a writing monkey.)
    A = (lon - lon0) * cos(lat)
    C = (e2 / (1 - e2)) * cos(lat) ** 2
    T = tan(lat) ** 2.0
    vlat = 1.0 / sqrt(1.0 - e2 * sin(lat) ** 2.0)
    slat = ((1.0 - (e2    / 4.0) - ((3.0 * e4)    / 64)   - ((5.0  * e6) / 256.0))  * lat -
            (((3.0 * e2)  / 8.0) + ((3.0 * e4)    / 32.0) + ((45.0 * e6) / 1024.0)) * sin(lat * 2.0) +
            (((15.0 * e4) / 256.0) + ((45.0 * e6) / 1024.0)) *
            sin(lat * 4.0) - ((35.0 * e6) / 3072.0) * sin(lat * 6.0))

    E = (500.0 + (K0 * a * vlat) * (A + (1.0 - T + C) *
         ((A ** 3.0) / 6.0) + (5.0 - 18.0 * T + T**2) * ((A ** 5.0) / 120.0)))
    N = (N0 + (K0 * a) * (slat + vlat * tan(lat) *
         (A ** 2.0 / 2.0 + (5.0 - T + 9.0 * C + 4.0 * C ** 2.0) *
         (A ** 4.0 / 24.0) + (61.0 - 58.0 * T + T ** 2) * A ** 6.0 / 720.0)))
    return E, N

## for testing
#if __name__ == "__main__":
#    read("/data/downloads/osm_parser/map.osm", bpy.context)


# ----------------------------------------------------------------------------
# blender integration

from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from bpy.props import StringProperty, FloatProperty, BoolProperty


class ImportOSM(Operator, ImportHelper):
    """Import OSM"""
    #bl_idname = "import.open_street_map"
    bl_idname = "import_mesh.osm"
    bl_label = "Import OpenStreetMap (.osm)"

    # ExportHelper mixin class uses this
    filename_ext = ".osm"
    filter_glob = StringProperty(
            default="*.osm",
            options={'HIDDEN'},
            )
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    scale = FloatProperty(
            name="Scale",
            default=100.0,
            )
    utm = BoolProperty(
            name="in UTM coordinates",
            default=True,
            )
    tag = BoolProperty(
            name="retrieve .osm tags as vertex groups",
            default=False,
            )

    def execute(self, context):
        return read(context, self.filepath, self.scale, self.tag, self.utm)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ImportOSM.bl_idname)


def register():
    bpy.utils.register_class(ImportOSM)
    bpy.types.INFO_MT_file_import.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportOSM)
    bpy.types.INFO_MT_file_import.remove(menu_func_export)
