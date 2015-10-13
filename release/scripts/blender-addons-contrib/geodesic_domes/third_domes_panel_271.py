import bpy
import os
from geodesic_domes import vefm_271 
from geodesic_domes import forms_271
from geodesic_domes import geodesic_classes_271
from geodesic_domes import add_shape_geodesic

from bpy.props import EnumProperty, IntProperty, FloatProperty, StringProperty, BoolProperty
#PKHG>NEEDED??? import math
from math import pi
from mathutils import Vector #needed to check vertex.vector values
"""
not in Blender 2.7*???
try:
    breakpoint = bpy.types.bp.bp
except:
    print("add breakpoint addon!")
"""        

########global######
last_generated_object = None
last_imported_mesh = None
basegeodesic = None
imported_hubmesh_to_use = None
########global end######

########EIND FOR SHAPEKEYS######
### error messages?!
bpy.types.Scene.error_message = StringProperty(name="actual error", default = "")    


bpy.types.Scene.geodesic_not_yet_called = BoolProperty(name="geodesic_not_called",default = True)

bpy.types.Scene.gd_help_text_width = IntProperty(name = "Text Width" , description = "The width above which the text wraps" , default = 60 , max = 180 , min = 20)

class Geodesic_Domes_Operator_Panel(bpy.types.Panel):
    """start a GD object here"""
    bl_label = "Geodesic Domes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS" #UI possible too
    bl_context = "objectmode"
    bl_category = "Create"
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self,context):
        sce = context.scene
        layout = self.layout
        col = layout.column()
        col.label("Geodesic Domes: ")
        col.operator(GenerateGeodesicDome.bl_idname, "create one!")
            
class GenerateGeodesicDome(bpy.types.Operator):
    bl_label = "Modify Geodesic Objects"
    bl_idname = "mesh.generate_geodesic_dome"
    bl_description = "Create object dependent on selection"
    bl_options = {'REGISTER', 'UNDO'}

#PKHG_NEW saving and loading parameters
    save_parameters = BoolProperty(name = "save params",\
           description = "activation save */tmp/GD_0.GD", default = False)
    load_parameters  = BoolProperty(name = "load params",\
           description = "read */tmp/GD_0.GD", default = False)

    gd_help_text_width = IntProperty(name = "Text Width" , description = "The width above which the text wraps" , default = 60 , max = 180 , min = 20)

    
    mainpages = EnumProperty(
    name="Menu",
    description="Create Faces, Struts & Hubs",
    items=[("Main", "Main", "Geodesic objects"),
           ("Faces", "Faces", "Generate Faces"),
           ("Struts", "Struts", "Generate Struts"),
           ("Hubs", "Hubs", "Generate Hubs"),
           ("Help", "Help", "Not implemented"),
          ],
    default='Main')

#for Faces!
    facetype_menu = EnumProperty(
    name="Faces",
    description="choose a facetype",
    items=[("0", "strip", "strip"),
           ("1", "open vertical", "vertical"),
           ("2", "opwn slanted", "slanted"),
           ("3", "closed point", "closed point"),
           ("4", "pillow", "pillow"),
           ("5", "closed vertical", "closed vertical"),
           ("6", "stepped", "stepped"),
           ("7", "spikes", "spikes"),
           ("8", "boxed", "boxed"),
           ("9", "diamond", "diamond"),
           ("10", "bar", "bar"),
          ],
    default='0')

    facetoggle = BoolProperty(name="Activate: Face Object", description = "Activate Faces for Geodesic object", default = False )
#    faceimporttoggle = BoolProperty(name="faceimporttoggle", default = False )
    face_use_imported_object = BoolProperty(name="Use: Imported Object",\
                description = "Activate faces on your Imported object",	default = False)
    facewidth = FloatProperty(name="facewidth", min = -1, soft_min = 0.001,  max = 4, default = .50)
    fwtog = BoolProperty(name="fwtog", default = False )
    faceheight = FloatProperty(name="faceheight", min = 0.001, max = 4, default = 1 )
    fhtog = BoolProperty(name="fhtog", default = False )
    face_detach = BoolProperty(name="face_detach", default = False )
    fmeshname = StringProperty(name="fmeshname", default = "defaultface")


    geodesic_types = EnumProperty(
        name="Objects", 
        description="Choose Geodesic, Grid, Cylinder, Parabola,\
                     Torus, Sphere, Import your mesh or Superparameters",
    items=[("Geodesic", "Geodesic", "Generate Geodesic"),
           ("Grid", "Grid", "Generate Grid"),
           ("Cylinder", "Cylinder", "Generate Cylinder"),
           ("Parabola", "Parabola", "Generate Parabola"),
           ("Torus", "Torus", "Generate Torus"),
           ("Sphere", "Sphere", "Generate Sphere"),
           ("Import your mesh", "Import your mesh", "Import Your Mesh"),
          ],
    default = 'Geodesic')

    import_mesh_name = StringProperty(name = "mesh to import",\
            description = "the name has to be the name of a meshobject", default = "None") 

    base_type = EnumProperty(
    name="Hedron",
    description="Choose between Tetrahedron, Octahedron, Icosahedron ",\
        items=[("Tetrahedron", "Tetrahedron", "Generate Tetrahedron"),\
               ("Octahedron", "Octahedron", "Generate Octahedron"),\
               ("Icosahedron", "Icosahedron", "Generate Icosahedron"),
           ],
    default='Tetrahedron')

    orientation = EnumProperty(
    name="Point^",
    description="Point (Vert), Edge or Face pointing upwards",
    items=[("PointUp", "PointUp", "Point up"),
           ("EdgeUp", "EdgeUp", "Edge up"),
           ("FaceUp", "FaceUp", "Face up"),
           ],
    default='PointUp')

    geodesic_class = EnumProperty(
    name="Class",
    description="Subdivide Basic/Triacon",
    items=[("Class 1", "Class 1", "class one"),
           ("Class 2", "Class 2", "class two"),
           ],
    default='Class 1')

    tri_hex_star = EnumProperty(
    name="Shape",
    description="Choose between tri hex star face types",
    items=[("tri", "tri", "tri faces"),
           ("hex", "hex", "hex faces(by tri)"),
           ("star", "star", "star faces(by tri)"),
              ],
    default='tri')

    spherical_flat = EnumProperty(
    name="Round",
    description="Choose between spherical or flat ",
    items=[("spherical", "spherical", "Generate spherical"),
           ("flat", "flat", "Generate flat"),
              ],
    default='spherical')

    use_imported_mesh = BoolProperty(name="use import",\
                    description = "Use an imported mesh", default = False)

#Cylinder
    cyxres= IntProperty(name="Resolution x/y", min = 3, max = 32,\
              description = "number of faces around x/y", default = 5 )
    cyyres= IntProperty(name="Resolution z", min = 3, max = 32,\
              description = "number of faces in z direction", default = 5 )
    cyxsz= FloatProperty(name="Scale x/y", min = 0.01, max = 10,\
	          description = "scale in x/y direction", default = 1 )
    cyysz= FloatProperty(name="Scale z", min = 0.01, max = 10,\
              description = "scale in z direction", default = 1 )    
    cyxell= FloatProperty(name="Stretch x",  min = 0.001, max = 4,\
              description = "stretch in x direction", default = 1 )
    cygap= FloatProperty(name="Gap",  min = -2, max = 2,\
              description = "shrink in % around radius", default = 1 )
    cygphase= FloatProperty(name="Phase", min = -4, max = 4,\
              description = "rotate around pivot x/y", default = 0 )
#Parabola
    paxres= IntProperty(name="Resolution x/y",  min = 3, max = 32,\
           description = "number of faces around x/y", default = 5 )
    payres= IntProperty(name="Resolution z",  min = 3, max = 32,\
           description = "number of faces in z direction", default = 5 )
    paxsz= FloatProperty(name="Scale x/y", min = 0.001, max = 10,\
           description = "scale in x/y direction", default = 0.30)
    paysz= FloatProperty(name="Scale z", min = 0.001, max = 10,\
           description = "scale in z direction",	default = 1 )
    paxell= FloatProperty(name="Stretch x", min = 0.001, max = 4,\
           description = "stretch in x direction",	default = 1 )
    pagap= FloatProperty(name="Gap", min = -2, max = 2,\
           description = "shrink in % around radius",	default = 1 )
    pagphase= FloatProperty(name="Phase", min = -4, max = 4,\
           description = "rotate around pivot x/y",	default = 0 )
#Torus            
    ures= IntProperty(name="Resolution x/y",min = 3, max = 32,\
           description = "number of faces around x/y", default = 8 )
    vres= IntProperty(name="Resolution z", min = 3, max = 32,\
            description = "number of faces in z direction", default = 8 )
    urad= FloatProperty(name="Radius x/y", min = 0.001, max = 10,\
            description = "radius in x/y plane",	default = 1 )
    vrad= FloatProperty(name="Radius z", min = 0.001, max = 10,\
            description = "radius in z plane",	default = 0.250)
    uellipse= FloatProperty(name="Stretch x", min = 0.001, max = 10,\
            description = "number of faces in z direction",	default = 1 )
    vellipse= FloatProperty(name="Stretch z", min = 0.001, max = 10,\
            description = "number of faces in z direction",	default = 1 )
    upart= FloatProperty(name="Gap x/y", min = -4, max = 4,\
            description = "shrink faces around x/y",	default = 1 )
    vpart= FloatProperty(name="Gap z", min = -4, max = 4,\
            description = "shrink faces in z direction",	default = 1 )
    ugap= FloatProperty(name="Phase x/y",  min = -4, max = 4,\
           description = "rotate around pivot x/y", default = 0 )
    vgap= FloatProperty(name="Phase z",  min = -4, max = 4,\
           description = "rotate around pivot z", default = 0 )
    uphase= FloatProperty(name="uphase", min = -4, max = 4,\
            description = "number of faces in z direction",	default = 0 )
    vphase= FloatProperty(name="vphase",  min = -4, max = 4,\
            description = "number of faces in z direction",	default = 0 )
    uexp= FloatProperty(name="uexp",  min = -4, max = 4,\
            description = "number of faces in z direction",	default = 0 )
    vexp= FloatProperty(name="vexp",  min = -4, max = 4,\
            description = "number of faces in z direction",	default = 0 )
    usuper= FloatProperty(name="usuper", min = -4, max = 4,\
           description = "first set of superform parameters",  default = 2 )
    vsuper= FloatProperty(name="vsuper",  min = -4, max = 4,\
            description = "second set of superform parameters", default = 2 )
    utwist= FloatProperty(name="Twist x/y", min = -4, max = 4,\
            description = " use with superformular u",	default = 0 )
    vtwist= FloatProperty(name="Twist z", min = -4, max = 4,\
            description = "use with superformular v",	default = 0 )

#Sphere 
    bures= IntProperty(name="Resolution x/y", min = 3, max = 32,\
            description = "number of faces around x/y",	default = 8 )
    bvres= IntProperty(name="Resolution z", min = 3, max = 32,\
            description = "number of faces in z direction",	default = 8 )
    burad= FloatProperty(name="Radius",  min = -4, max = 4,\
            description = "overall radius",	default = 1 )
    bupart= FloatProperty(name="Gap x/y", min = -4, max = 4,\
            description = "shrink faces around x/y",	default = 1 )
    bvpart= FloatProperty(name="Gap z", min = -4, max = 4,\
            description = "shrink faces in z direction",	default = 1 )
    buphase= FloatProperty(name="Phase x/y",  min = -4, max = 4,
            description = "rotate around pivot x/y",	default = 0 )
    bvphase= FloatProperty(name="Phase z", min = -4, max = 4,\
            description = "rotate around pivot z",	default = 0 )
    buellipse= FloatProperty(name="Stretch x", min = 0.001, max = 4,\
            description = "stretch in the x direction",	default = 1 )
    bvellipse= FloatProperty(name="Stretch z", min = 0.001, max = 4,\
            description = "stretch in the z direction",	default = 1 )
#Grid    
    grxres = IntProperty(name="Resolution x", min = 2, soft_max = 10, max = 20,\
                         description = "number of faces in x direction", default = 5 )
    gryres = IntProperty(name="Resolution z",min = 2, soft_min = 2, soft_max=10, max = 20,\
                         description = "number of faces in x direction", default = 2)
    grxsz = FloatProperty(name = "X size", min = 1, soft_min=0.01, soft_max=5, max = 10,\
                         description = "x size", default = 2.0)
    grysz = FloatProperty(name="Y size",min = 1, soft_min=0.01, soft_max=5, max = 10,\
                         description = "y size", default = 1.0)

#PKHG_TODO_??? what means cart
    cart = IntProperty(name = "cart",min = 0, max = 2,  default = 0)
    frequency = IntProperty(name="Frequency", min = 1, max = 8,\
                           description ="subdivide base triangles", default = 1 )
    eccentricity = FloatProperty(name = "Eccentricity",  min = 0.01 , max = 4,\
                 description = "scaling in x/y dimension", default = 1 )
    squish = FloatProperty(name = "Squish",min = 0.01, soft_max = 4, max = 10,\
                 description = "scaling in z dimension",  default = 1 )
    radius = FloatProperty(name = "Radius",min = 0.01, soft_max = 4, max = 10,\
                 description = "overall radius",  default = 1 )
    squareness = FloatProperty(name="Square x/y", min = 0.1, max = 5,\
                 description = "superelipse action in x/y", default = 2 )
    squarez = FloatProperty(name="Square z", min = 0.1, soft_max = 5, max = 10,\
                 description = "superelipse action in z", default = 2 )
    baselevel = IntProperty(name="baselevel", default = 5 )
    dual = BoolProperty(name="Dual", description = "faces become verts,\
                        verts become faces, edges flip", default = False)
    rotxy = FloatProperty(name="Rotate x/y", min= -4, max = 4,\
                 description = "rotate superelipse action in x/y", default = 0 )
    rotz = FloatProperty(name="Rotate z",  min= -4, max = 4,\
                 description = "rotate superelipse action in z", default = 0 )

#for choice of superformula
    uact = BoolProperty(name = 'superformula u (x/y)',\
                        description = "activate superformula u parameters", default = False)
    vact = BoolProperty(name = 'superformula v (z)',\
                        description = "activate superformula v parameters", default = False)
    um = FloatProperty(name = 'um', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  3)
    un1 = FloatProperty(name = 'un1', min = 0, soft_min=0.1, soft_max=5,max = 20,\
                 description = "to do",	default =  1)
    un2 = FloatProperty(name = 'un2', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    un3 = FloatProperty(name = 'un3', min = 0,   soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    ua = FloatProperty(name = 'ua', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1.0)
    ub = FloatProperty(name = 'ub', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  4.0)
    vm = FloatProperty(name = 'vm', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    vn1 = FloatProperty(name = 'vn1', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    vn2 = FloatProperty(name = 'vn2', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    vn3 = FloatProperty(name = 'vn3', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    va = FloatProperty(name = 'va', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)
    vb = FloatProperty(name = 'vb', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  1)

    uturn = FloatProperty(name = 'uturn', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  0)
    vturn = FloatProperty(name = 'vturn', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  0)
    utwist = FloatProperty(name = 'utwist', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  0)
    vtwist = FloatProperty(name = 'vtwist', min = 0, soft_min=0.1, soft_max=5,max = 10,\
                 description = "to do",	default =  0)

#Strut
    struttype= IntProperty(name="struttype", default= 0)
    struttoggle = BoolProperty(name="struttoggle", default = False )
    strutimporttoggle= BoolProperty(name="strutimporttoggle", default = False )
    strutimpmesh= StringProperty(name="strutimpmesh", default = "None")
    strutwidth= FloatProperty(name="strutwidth", min = -10, soft_min = 5, soft_max = 5,\
                              max = 10, default = 1 )
    swtog= BoolProperty(name="swtog", default = False )
    strutheight= FloatProperty(name="strutheight", min = -5, soft_min = -1, soft_max = 5,\
                               max = 10, default = 1 )
    shtog= BoolProperty(name="shtog", default = False )
    strutshrink= FloatProperty(name="strutshrink", min = 0.001, max = 4, default = 1 )
    sstog= BoolProperty(name="sstog", default = False )
    stretch= FloatProperty(name="stretch",  min= -4, max = 4, default = 1.0 )
    lift= FloatProperty(name="lift", min = 0.001, max = 10, default = 0 )
    smeshname= StringProperty(name="smeshname", default = "defaultstrut")

#Hubs
    hubtype = BoolProperty(name ="hubtype", description = "not used", default = True )
    hubtoggle = BoolProperty(name ="hubtoggle", default = False )
    hubimporttoggle = BoolProperty(name="new import", description = "import a mesh",\
                                   default = False )
    hubimpmesh = StringProperty(name="hubimpmesh",\
                 description = "name of mesh to import",  default = "None")
    hubwidth = FloatProperty(name="hubwidth", min = 0.01, max = 10,\
                 default = 1 )
    hwtog = BoolProperty(name="hwtog", default = False )
    hubheight = FloatProperty(name="hubheight", min = 0.01, max = 10,\
                 default = 1 )
    hhtog = BoolProperty(name="hhtog", default = False )
    hublength = FloatProperty(name ="hublength", min  = 0.1, max  = 10,\
                 default  = 1 )
    hstog= BoolProperty(name="hstog", default = False )
    hmeshname= StringProperty(name="hmeshname",\
                              description = "Name of an existing mesh needed!", default = "None")

    name_list = ['facetype_menu','facetoggle','face_use_imported_object',
'facewidth','fwtog','faceheight','fhtog',
'face_detach','fmeshname','geodesic_types','import_mesh_name',
'base_type','orientation','geodesic_class','tri_hex_star',
'spherical_flat','use_imported_mesh','cyxres','cyyres',
'cyxsz','cyysz','cyxell','cygap',
'cygphase','paxres','payres','paxsz',
'paysz','paxell','pagap','pagphase',
'ures','vres','urad','vrad',
'uellipse','vellipse','upart','vpart',
'ugap','vgap','uphase','vphase',
'uexp','vexp','usuper','vsuper',
'utwist','vtwist','bures','bvres',
'burad','bupart','bvpart','buphase',
'bvphase','buellipse','bvellipse','grxres',
'gryres','grxsz','grysz',
'cart','frequency','eccentricity','squish',
'radius','squareness','squarez','baselevel',
'dual','rotxy','rotz',
'uact','vact','um','un1',
'un2','un3','ua','ub',
'vm','vn1','vn2','vn3',
'va','vb','uturn','vturn',
'utwist','vtwist','struttype','struttoggle',
'strutimporttoggle','strutimpmesh','strutwidth','swtog',
'strutheight','shtog','strutshrink','sstog',
'stretch','lift','smeshname','hubtype',
'hubtoggle','hubimporttoggle','hubimpmesh','hubwidth',
'hwtog','hubheight','hhtog','hublength',
'hstog','hmeshname']    

    def write_params(self,filename):
        file = open(filename, "w", encoding="utf8", newline="\n")
        fw = file.write
    #for Faces!
        for el in self.name_list:
            fw(el + ", ")
            fw(repr(getattr(self,el)))
            fw(",\n")
        file.close()

    def read_file(self,filename):
        file = open(filename, "r", newline="\n")
        result = []
        line = file.readline()
        while(line):
            tmp = line.split(", ")
            result.append(eval(tmp[1]))
            line = file.readline()
        return result
    

    def draw(self,context):
        sce = context.scene
        layout = self.layout
        row = layout.row()
        row.prop(self, "save_parameters")
        row.prop(self, "load_parameters")
        col = layout.column()
        col.label(" ")
        col.prop(self, "mainpages")
        which_mainpages = self.mainpages
        if which_mainpages == 'Main':
            col = layout.column()
            col.prop(self, "geodesic_types")
            tmp = self.geodesic_types
            if tmp == "Geodesic":
                col.label(text="Geodesic Object Types:")
                col.prop(self, "geodesic_class")                
                col.prop(self, "base_type")
                col.prop(self, "orientation")
                col.prop(self, "tri_hex_star")
                col.prop(self, "spherical_flat")
                col.label("Geodesic Object Parameters:")
                row = layout.row()
                row.prop(self, "frequency")
                row = layout.row()
                row.prop(self, "radius")
                row = layout.row()
                row.prop(self, "eccentricity")
                row = layout.row()
                row.prop(self, "squish")
                row = layout.row()
                row.prop(self, "squareness")
                row = layout.row()
                row.prop(self, "squarez")
                row = layout.row()
                row.prop(self, "rotxy")
                row = layout.row()
                row.prop(self, "rotz")
                row = layout.row()
                row.prop(self, "dual")
            elif tmp == 'Torus':
                col.label("Torus Parameters")
                row = layout.row()
                row.prop(self, "ures")
                row = layout.row()
                row.prop(self, "vres")
                row = layout.row()
                row.prop(self, "urad")
                row = layout.row()
                row.prop(self, "vrad")
                row = layout.row()
                row.prop(self, "uellipse")
                row = layout.row()
                row.prop(self, "vellipse")
                row = layout.row()
                row.prop(self, "upart")
                row = layout.row()
                row.prop(self, "vpart")
                row = layout.row()
                row.prop(self, "ugap")
                row.prop(self, "vgap")
                row = layout.row()
                row.prop(self, "uphase")
                row.prop(self, "vphase")
                row = layout.row()
                row.prop(self, "uexp")
                row.prop(self, "vexp")
                row = layout.row()
                row.prop(self, "usuper")
                row.prop(self, "vsuper")
                row = layout.row()
                row.prop(self, "vgap")
                row = layout.row()
            elif tmp == 'Sphere':
                col.label("Sphere Parameters")
                row = layout.row()
                row.prop(self, "bures")
                row = layout.row()
                row.prop(self, "bvres")
                row = layout.row()
                row.prop(self, "burad")
                row = layout.row()                
                row.prop(self, "bupart")
                row = layout.row()
                row.prop(self, "buphase")
                row = layout.row()
                row.prop(self, "bvpart")
                row = layout.row()
                row.prop(self, "bvphase")
                row = layout.row()
                row.prop(self, "buellipse")
                row = layout.row()
                row.prop(self, "bvellipse")
            elif tmp == 'Parabola':
                col.label("Parabola Parameters")
                row = layout.row()
                row.prop(self, "paxres")
                row = layout.row()
                row.prop(self, "payres")
                row = layout.row()
                row.prop(self, "paxsz")
                row = layout.row()
                row.prop(self, "paysz")
                row = layout.row()
                row.prop(self, "paxell")
                row = layout.row()
                row.prop(self, "pagap")
                row = layout.row()
                row.prop(self, "pagphase")
            elif tmp == 'Cylinder':
                col.label("Cylinder Parameters")
                col.prop(self, "cyxres")
                col.prop(self, "cyyres")
                col.prop(self, "cyxsz")
                col.prop(self, "cyysz")
                col.prop(self, "cyxell")
                col.prop(self, "cygap")
                col.prop(self, "cygphase")
            elif tmp == 'Grid':
                col.label("Grid Parameters")
                row = layout.row()
                row.prop(self, "grxres")
                row = layout.row()
                row.prop(self, "gryres")
                row = layout.row()
                row.prop(self, "grxsz")
                row = layout.row()
                row.prop(self, "grysz")
            elif tmp == 'Import your mesh':
                col.prop(self, "use_imported_mesh")
                col.prop(self, "import_mesh_name")
#######superform parameters only where possible
            row = layout.row()
            row.prop(self, "uact")
            row = layout.row()
            row.prop(self, "vact")                
            row = layout.row()
            if not(tmp == 'Import your mesh'):
                if (self.uact == False) and (self.vact == False):
                    row.label("no checkbox active!")
                else:
                    row.label("Superform Parameters")
                if self.uact:
                    row = layout.row()
                    row.prop(self, "um")
                    row = layout.row()
                    row.prop(self, "un1")
                    row = layout.row()
                    row.prop(self, "un2")
                    row = layout.row()
                    row.prop(self, "un3")
                    row = layout.row()
                    row.prop(self, "ua")
                    row = layout.row()
                    row.prop(self, "ub")
                    row = layout.row()
                    row.prop(self, "uturn")
                    row = layout.row()
                    row.prop(self, "utwist")
                if self.vact:
                    row = layout.row()
                    row.prop(self, "vm")
                    row = layout.row()
                    row.prop(self, "vn1")
                    row = layout.row()
                    row.prop(self, "vn2")
                    row = layout.row()
                    row.prop(self, "vn3")
                    row = layout.row()
                    row.prop(self, "va")
                    row = layout.row()
                    row.prop(self, "vb")
                    row = layout.row()
                    row.prop(self, "vturn")
                    row = layout.row()
                    row.prop(self, "vtwist")                
########einde superform
        elif  which_mainpages == "Hubs":
            row = layout.row()
            row.prop(self, "hubtoggle")
#PKHG_NOT_USDED_YET_24-11            row.prop(self, "hubtype")
            row = layout.row()            
#25-11 not needed            row.prop(self, "hubimporttoggle")
            row = layout.row()
            if self.hubimpmesh == "None":
                row = layout.row()
                row.label("name of a hub to use")
                row = layout.row()
            row.prop(self, "hubimpmesh")
            row = layout.row()
            if self.hmeshname == "None":
                row = layout.row()
                row.label("name of mesh to be filled in!")
                row = layout.row()
            row.prop(self, "hmeshname")
            row = layout.row()
            row.prop(self, "hwtog")
            if self.hwtog:
                row.prop(self, "hubwidth")
            row = layout.row()
            row.prop(self, "hhtog")
            if self.hhtog:
                row.prop(self, "hubheight")
            row = layout.row()
            row.prop(self, "hublength")                
        elif which_mainpages == "Struts":
            row = layout.row()
            row.prop(self, "struttype")
            row.prop(self, "struttoggle")
#            row = layout.row()            
#            row.prop(self, "strutimporttoggle")
            row = layout.row()            
            row.prop(self, "strutimpmesh")
            row = layout.row()
            row.prop(self, "swtog")
            if self.swtog:
                row.prop(self, "strutwidth")
            row = layout.row()
            row.prop(self, "shtog")
            if self.shtog:
                row.prop(self, "strutheight")
            row = layout.row()
            row.prop(self, "sstog")
            if self.sstog:
               row.prop(self, "strutshrink")
            row = layout.row()               
            row.prop(self, "stretch")
            row = layout.row()            
            row.prop(self, "lift")
            row = layout.row()            
            row.prop(self, "smeshname")
        elif which_mainpages == "Faces":
            row = layout.row()
            row.prop(self, "facetoggle")
            row = layout.row()
            row.prop(self, "face_use_imported_object")
            row = layout.row()
            row.prop(self, "facetype_menu")
            row = layout.row()
            row.prop(self, "fwtog")
            if self.fwtog:
                row.prop(self, "facewidth")
            row = layout.row()
            row.prop(self, "fhtog")
            if self.fhtog:
                row.prop(self, "faceheight")
            row = layout.row()
            row.prop(self, "face_detach")
            row = layout.row()
            row.prop(self, "fmeshname")
            row = layout.row()
        
        #help menu GUI
        elif which_mainpages == "Help":
            import textwrap

            # a function that allows for multiple labels with text that wraps
            # you can allow the user to set where the text wraps with the 
            # text_width parameter
            # other parameters are ui : here you usually pass layout
            # text: is a list with each index representing a line of text
            
            def multi_label(text, ui,text_width=120):
                for x in range(0,len(text)):
                    el = textwrap.wrap(text[x], width = text_width )
            
                    for y in range(0,len(el)):
                        ui.label(text=el[y])

            box = layout.box() 
            help_text = ["NEW!", 
                "New facility: save or load (nearly all) parameters",
                 "A file GD_0.GD will be used, living in:",
                 "geodesic_domes/tmp",
                 "--------",
                 "After loading you have to change a ",
                 "parameter back and forth"
                 "to see it"]
            text_width = self.gd_help_text_width
            box.prop(self, "gd_help_text_width",slider=True)
            multi_label(help_text,box, text_width)

    def execute(self, context):
        global last_generated_object, last_imported_mesh, basegeodesic, imported_hubmesh_to_use 
        #default superformparam = [3, 10, 10, 10, 1, 1, 4, 10, 10, 10, 1, 1, 0, 0, 0.0, 0.0, 0, 0]]
        superformparam = [self.um, self.un1, self.un2, self.un3, self.ua,\
                          self.ub, self.vm, self.vn1, self.vn2, self.vn3,\
                          self.va, self.vb, self.uact, self.vact,\
                          self.uturn*pi, self.vturn*pi, \
                          self.utwist, self.vtwist]
        context.scene.error_message = "" 
        if self.mainpages == 'Main':
            if self.geodesic_types == "Geodesic":
                tmp_fs = self.tri_hex_star
                faceshape = 0 # tri!
                if tmp_fs == "hex":
                    faceshape = 1
                elif tmp_fs == "star":
                    faceshape = 2
                tmp_cl = self.geodesic_class
                klass = 0
                if tmp_cl == "Class 2":
                    klass = 1
                shape = 0 
                parameters = [self.frequency, self.eccentricity, self.squish,\
                          self.radius, self.squareness, self.squarez, 0,\
                          shape, self.baselevel, faceshape, self.dual,\
                          self.rotxy, self.rotz, klass, superformparam]               
                basegeodesic =  creategeo(self.base_type,self.orientation,parameters)
                basegeodesic.makegeodesic()
                basegeodesic.connectivity()
                mesh = vefm_271.mesh()                
                vefm_271.finalfill(basegeodesic,mesh) #always! for hexifiy etc. necessarry!!!                     
                vefm_271.vefm_add_object(mesh)
                last_generated_object = context.active_object
                last_generated_object.location  = (0,0,0)
                context.scene.objects.active = last_generated_object            
            elif self.geodesic_types == 'Grid':
                basegeodesic = forms_271.grid(self.grxres,self.gryres,\
                       self.grxsz,self.grysz,1.0,1.0,0,0,0,\
                                      0,1.0,1.0,superformparam)
                vefm_271.vefm_add_object(basegeodesic)
                bpy.data.objects[-1].location = (0,0,0)
            elif self.geodesic_types == "Cylinder":
                basegeodesic = forms_271.cylinder(self.cyxres, self.cyyres, \
                                   self.cyxsz, self.cyysz, self.cygap, \
                                   1.0, self.cygphase, 0, 0, 0, self.cyxell,\
                                   1.0, superformparam)
                vefm_271.vefm_add_object(basegeodesic)
                bpy.data.objects[-1].location = (0,0,0)                
                
            elif self.geodesic_types == "Parabola":
                basegeodesic=forms_271.parabola(self.paxres, self.payres,\
                    self.paxsz, self.paysz, self.pagap,1.0, self.pagphase,\
                    0,0,0, self.paxell,1.0,superformparam)
                vefm_271.vefm_add_object(basegeodesic)
                bpy.data.objects[-1].location = (0,0,0)                
            elif self.geodesic_types == "Torus":
                basegeodesic = forms_271.torus(self.ures, self.vres,\
                       self.vrad, self.urad, self.upart, self.vpart,\
                       self.ugap, self.vgap,0,0, self.uellipse,\
                       self.vellipse, superformparam)
                vefm_271.vefm_add_object(basegeodesic)
                bpy.data.objects[-1].location = (0,0,0)
            elif self.geodesic_types == "Sphere":
                basegeodesic=forms_271.sphere(self.bures, self.bvres,\
                        self.burad,1.0, self.bupart, self.bvpart,\
                        self.buphase, self.bvphase,0,0, self.buellipse,\
                        self.bvellipse,superformparam)	

                vefm_271.vefm_add_object(basegeodesic)
                bpy.data.objects[-1].location = (0,0,0)                
            elif self.geodesic_types == "Import your mesh":
                obj_name = self.import_mesh_name
                if obj_name == "None":
                    message = "fill in a name \nof an existing mesh\nto be imported"
                    context.scene.error_message = message
                    self.report({"INFO"}, message)
                    print("***INFO*** you have to fill in the name of an existing mesh")
                else:
#                    obj_in_scene = context.objects
                    names = [el.name for el in context.scene.objects]
                    if obj_name in names and context.scene.objects[obj_name].type == "MESH":
                        obj = context.scene.objects[obj_name]
#                        if obj.type == "MESH":                        
                        your_obj = vefm_271.importmesh(obj.name,False)
                        last_imported_mesh = your_obj
                        vefm_271.vefm_add_object(your_obj)
                        last_generated_object = bpy.context.active_object
                        last_generated_object.name ="Imported mesh"
                        bpy.context.active_object.location = (0,0,0)
                    else:
                        message = obj_name +" does not exist \nor is not a MESH"
                        context.scene.error_message = message                
                        bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
                        self.report({'ERROR'}, message)
                        print("***ERROR***" + obj_name +" does not exist or is not a MESH")
        elif self.mainpages == "Hubs":
            hubtype = self.hubtype
            hubtoggle =  self.hubtoggle
            hubimporttoggle = self.hubimporttoggle
            hubimpmesh = self.hubimpmesh
            hubwidth = self.hubwidth
            hwtog = self.hwtog
            hubheight = self.hubheight
            hhtog = self.hhtog
            hublength = self.hublength
            hstog =  self.hstog
            hmeshname=  self.hmeshname
#PKHG_TODO_27-11 better info!??
            if not (hmeshname == "None") and not (hubimpmesh == "None") and  hubtoggle:                
                try:                    
                    print("\nDBG third_domes L799 hmeshname= ", hmeshname)
                    hub_obj = vefm_271.importmesh(hmeshname,0)
                    print("\nDBG third_domes L801 hub_obj = ", hub_obj.faces[:])
                    hub = vefm_271.hub(hub_obj, True,\
                            hubwidth, hubheight, hublength,\
                              hwtog, hhtog, hstog, hubimpmesh)
                    print("\nDBG third_domes L805 de hub: ", hub)
                    mesh = vefm_271.mesh("test")
                    vefm_271.finalfill(hub,mesh)
                    vefm_271.vefm_add_object(mesh)
                    bpy.data.objects[-1].location = (0,0,0)
                except:
                    message = "***ERROR third_domes_panel L811 *** \neither no mesh for hub\nor " + hmeshname +  " available"                    
                    context.scene.error_message = message
                    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
                    print(message)                
            else:
                message = "***INFO***\nuse the hub toggle!"
                context.scene.error_message = message
                print("\n***INFO*** use the hub toggle!")
        elif self.mainpages == "Struts":
            struttype = self.struttype
            struttoggle = self.struttoggle
            strutimporttoggle = self.strutimporttoggle
            strutimpmesh = self.strutimpmesh
            strutwidth = self.strutwidth
            swtog = self.swtog
            strutheight = self.strutheight
            shtog = self.shtog
            strutshrink = self.strutshrink
            sstog = self.sstog
            stretch = self.stretch
            lift = self.lift
            smeshname = self.smeshname
            if not (strutimpmesh == "None") and struttoggle:
                names = [el.name for el in context.scene.objects]
                if strutimpmesh in names and context.scene.objects[strutimpmesh].type == "MESH":
                    strut = vefm_271.strut(basegeodesic, struttype, strutwidth,\
                                           strutheight, stretch, swtog, shtog, swtog,\
                                           strutimpmesh, sstog, lift)
                    strutmesh = vefm_271.mesh()
                    vefm_271.finalfill(strut,strutmesh)
                    vefm_271.vefm_add_object(strutmesh)
                    last_generated_object = context.active_object
                    last_generated_object.name = smeshname
                    last_generated_object.location  = (0,0,0)
                else:
                    message = "***ERROR***\n" + strutimpmesh + "\nis not a MESH"
                    context.scene.error_message = message
                    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
                    print("***ERROR*** strut obj is not a MESH")
            else:
                vefm_271.vefm_add_object(basegeodesic)
        elif self.mainpages == "Faces":
            if self.facetoggle:
                faceparams=[[self.face_detach,0,[[0.5,0.0]]], #0 strip
                            [self.face_detach,0,[[0.0,0.5]]], #1 vertical
                            [self.face_detach,0,[[0.5,0.5]]], #2 slanted
                            [self.face_detach,1,[[0.25,0.25],[0.5,0.5]]], #3 closed point
                            [self.face_detach,1,[[0.1,0.03],[0.33,0.06],[0.0,0.1]]], #4 pillow
                            [self.face_detach,2,[[0.0,0.5]]], #5 closed vertical
                            [self.face_detach,2,[[0.0,0.25],[0.25,0.25],[0.25,0.5]]], #6 stepped
                            [self.face_detach,1,[[0.2,0.1],[0.4,0.2],[0.0,1.0]]], #7 spikes
                            [self.face_detach,3,[[0.25,0.0],[0.25,0.5],[0.0,0.5]]], #8 boxed 
                            [self.face_detach,3,[[0.25,0.5],[0.5,0.0],[0.25,-0.5]]], #9 diamond
                            [self.face_detach,4,[[0.5,0.0],[0.5,0.5],[0.0,0.5]]],] #10 bar
                facedata = faceparams[int(self.facetype_menu)]
                if not self.face_use_imported_object:
                    faceobject = vefm_271.facetype(basegeodesic, facedata, self.facewidth,\
                                                   self.faceheight,self.fwtog)
                else:
                    if last_imported_mesh: 
                        faceobject = vefm_271.facetype(last_imported_mesh, facedata,\
                                                       self.facewidth, self.faceheight, self.fwtog)
                    else:
                        message = "***ERROR***\nno imported message available\n" + "last geodesic used" 
                        context.scene.error_message = message
                        bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
                        print("\n***ERROR*** no imported mesh available")
                        print("last geodesic used!")
                        faceobject = vefm_271.facetype(basegeodesic,facedata,\
                                     self.facewidth,self.faceheight,self.fwtog)
                facemesh = vefm_271.mesh()
                finalfill(faceobject, facemesh)
                vefm_271.vefm_add_object(facemesh)
                obj = bpy.data.objects[-1]
                obj.name = self.fmeshname
                obj.location = (0,0,0)
#PKHG save or load (nearly) all parameters                
        if self.save_parameters:
            self.save_parameters = False
            try:
                scriptpath = bpy.utils.script_paths()[0]
                sep = os.path.sep
                tmpdir = os.path.join(scriptpath, "addons", "geodesic_domes" , "tmp")
#scriptpath + sep + "addons" + sep + "geodesic_domes" + sep + "tmp"                              
                if not os.path.isdir(tmpdir):
                    message = "***ERROR***\n" + tmpdir + "\nnot (yet) available"  
                    
                filename = tmpdir + sep + "GD_0.GD"
#        self.read_file(filename)
                try:
                    self.write_params(filename)
                    message = "***OK***\nparameters saved in\n" + filename
                    print(message)
                except:
                    message = "***ERRROR***\n" + "writing " + filename + "\nnot possible"
                #bpy.context.scene.instant_filenames = filenames
                
            except:
                message = "***ERROR***\n Contakt PKHG, something wrong happened"
                
            context.scene.error_message = message
            bpy.ops.object.dialog_operator('INVOKE_DEFAULT')

        if self.load_parameters:
            self.load_parameters = False
            try:
                scriptpath = bpy.utils.script_paths()[0]
                sep = os.path.sep
                tmpdir = os.path.join(scriptpath, "addons", "geodesic_domes" , "tmp")
                #PKHG>NEXT comment????
                #scriptpath + sep + "addons" + sep + "geodesic_domes" + sep + "tmp"                              
                if not os.path.isdir(tmpdir):
                    message = "***ERROR***\n" + tmpdir + "\nnot available"  
                    print(message)
                filename = tmpdir + sep + "GD_0.GD"
#        self.read_file(filename)
                try:
                    res = self.read_file(filename)
                    for i,el in enumerate(self.name_list):
                        setattr(self,el,res[i])
                    message = "***OK***\nparameters read from\n" + filename
                    print(message)
                except:
                    message = "***ERRROR***\n" + "writing " + filename + "\nnot possible"
                    #bpy.context.scene.instant_filenames = filenames
            except:
                message = "***ERROR***\n Contakt PKHG,\nsomething went wrong reading params happened"
            context.scene.error_message = message
            bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
        return {'FINISHED'}
    
    def invoke(self, context, event):
        global basegeodesic
        bpy.ops.view3d.snap_cursor_to_center()
        tmp = context.scene.geodesic_not_yet_called
        if tmp:            
            context.scene.geodesic_not_yet_called = False
        self.execute(context)
        return {'FINISHED'}

def creategeo(polytype,orientation,parameters):
    geo = None
    if polytype == "Tetrahedron":
        if orientation == "PointUp":
            geo = geodesic_classes_271.tetrahedron(parameters)
        elif orientation == "EdgeUp":
            geo=geodesic_classes_271.tetraedge(parameters)
        elif orientation == "FaceUp":
            geo=geodesic_classes_271.tetraface(parameters)
    elif polytype == "Octahedron": 
        if orientation == "PointUp":
            geo=geodesic_classes_271.octahedron(parameters)
        elif orientation == "EdgeUp":
            geo=geodesic_classes_271.octaedge(parameters)
        elif orientation == "FaceUp":
            geo=geodesic_classes_271.octaface(parameters)
    elif polytype == "Icosahedron":
        if orientation == "PointUp":
            geo=geodesic_classes_271.icosahedron(parameters)
        elif orientation == "EdgeUp":
            geo=geodesic_classes_271.icoedge(parameters)
        elif orientation == "FaceUp":
            geo=geodesic_classes_271.icoface(parameters)
    return geo
    
basegeodesic,fmeshname,smeshname,hmeshname,outputmeshname,strutimpmesh,hubimpmesh = [None]*7

def finalfill(source,target):
    count=0
    for point in source.verts:
        newvert = vefm_271.vertex(point.vector)
        target.verts.append(newvert)
        point.index = count
        count  += 1 
    for facey in source.faces:
        row=len(facey.vertices)
        if row >= 5:
            newvert = vefm_271.average(facey.vertices).centroid()
            centre = vefm_271.vertex(newvert.vector)
            target.verts.append(centre)
            for i in range(row):
                if i == row - 1:
                    a = target.verts[facey.vertices[-1].index]
                    b = target.verts[facey.vertices[0].index]
                else:
                    a = target.verts[facey.vertices[i].index]
                    b = target.verts[facey.vertices[i+1].index]
                c = centre
                f = [a,b,c]
                target.faces.append(f)
        else:
            f = []
            for j in range(len(facey.vertices)):

                a = facey.vertices[j]
                f.append(target.verts[a.index])
            target.faces.append(f)
        
###for error messages         
class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "INFO"

    def draw(self,context):
        layout = self.layout
        message = context.scene.error_message
        col = layout.column()
        tmp = message.split("\n")
        for el in tmp:
            col.label(el)
        
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
            

######### register all
def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

