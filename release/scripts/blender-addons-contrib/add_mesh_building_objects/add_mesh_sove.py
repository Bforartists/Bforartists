'''bl_info = {
    "name": "Sove",
    "author": "SayPRODUCTIONS",
    "version": (1, 0),
    "blender": (2, 59, 0),
    "location": "View3D > Add > Mesh > Say3D",
    "description": "Sove Framema",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}
'''
import bpy
from bpy.props import *
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
import operator
from math import pi, sin, cos, sqrt, atan

def MSVE():
    if 'Sove' not in bpy.data.materials:
        mtl=bpy.data.materials.new('Sove')
        mtl.diffuse_color     = (0.44,0.52,0.64)
        mtl.diffuse_shader    = 'LAMBERT'
        mtl.diffuse_intensity = 1.0
    else:
        mtl=bpy.data.materials['Sove']
    return mtl
def Prs(self,v1,v2,v3,v4,v5,v6,v7,v8,v9,fg,fh,fd,
        f0,f1,f2,f3,f4,f5,f6,f7,f8,f9):
    self.gen=v1;self.knr=v2;self.yuk=v3
    self.alt=v4;self.ust=v5;self.sdr=v6
    self.pdr=v7;self.dh =v8;self.dr =v9
    self.fg =fg;self.fh =fh;self.fd =fd
    self.f0 =f0;self.f1 =f1;self.f2 =f2;self.f3=f3;self.f4=f4
    self.f5 =f5;self.f6 =f6;self.f7 =f7;self.f8=f8;self.f9=f9
def add_object(self, context):
    fc=[];vr=[]
    mx =self.gen/200;my =self.yuk/100;k1=self.knr/100;dh=self.dh/100;fd=self.fd/100;fh=self.fh/100
    alt=self.alt/100;ust=my-self.ust/100;drn=-self.sdr/100;pdr=self.pdr/100
    vr.append([-mx-k1,  0,  0]);vr.append([ mx+k1,  0,  0]);vr.append([ mx+k1,  0, my]);vr.append([-mx-k1,  0, my])
    vr.append([-mx,   pdr,alt]);vr.append([ mx,   pdr,alt]);vr.append([ mx,   pdr,ust]);vr.append([-mx,   pdr,ust])
    vr.append([-mx-k1,drn,  0]);vr.append([ mx+k1,drn,  0]);vr.append([ mx+k1,drn, my]);vr.append([-mx-k1,drn, my])
    vr.append([-mx,   drn,alt]);vr.append([ mx,   drn,alt]);vr.append([ mx,   drn,ust]);vr.append([-mx,   drn,ust])
    fc.append([ 8, 0, 1, 9]);fc.append([ 8, 9,13,12])
    fc.append([12,13, 5, 4]);fc.append([11,10, 2, 3])
    if self.fg==0:
        fc.append([ 0, 8,11, 3]);fc.append([ 8,12,15,11]);fc.append([12, 4, 7,15])
        fc.append([ 5,13,14, 6]);fc.append([13, 9,10,14]);fc.append([ 9, 1, 2,10])
    else:
        fc.append([11, 3,16,17]);fc.append([15,11,17,18]);fc.append([ 7,15,18,24])
        fc.append([25,19,14, 6]);fc.append([19,20,10,14]);fc.append([20,21, 2,10])
        ou=self.fg*12
        fc.append([4,7,12+ou,24+ou]);fc.append([6,5,25+ou,13+ou])
    z=my
    for i in range(self.fg):
        if i==0:z-=self.f0/100
        if i==1:z-=self.f1/100
        if i==2:z-=self.f2/100
        if i==3:z-=self.f3/100
        if i==4:z-=self.f4/100
        if i==5:z-=self.f5/100
        if i==6:z-=self.f6/100
        if i==7:z-=self.f7/100
        if i==8:z-=self.f8/100
        if i==9:z-=self.f9/100
        vr.append([   -mx-k1,     0,z]);vr.append([   -mx-k1,   drn,z]);vr.append([     -mx,   drn,z])
        vr.append([       mx,   drn,z]);vr.append([    mx+k1,   drn,z]);vr.append([   mx+k1,     0,z])
        vr.append([-mx-k1+fd,     0,z]);vr.append([-mx-k1+fd,drn+fd,z]);vr.append([     -mx,drn+fd,z])
        vr.append([       mx,drn+fd,z]);vr.append([ mx+k1-fd,drn+fd,z]);vr.append([mx+k1-fd,     0,z])
        z-=fh
        vr.append([   -mx-k1,     0,z]);vr.append([   -mx-k1,   drn,z]);vr.append([     -mx,   drn,z])
        vr.append([       mx,   drn,z]);vr.append([    mx+k1,   drn,z]);vr.append([   mx+k1,     0,z])
        vr.append([-mx-k1+fd,     0,z]);vr.append([-mx-k1+fd,drn+fd,z]);vr.append([     -mx,drn+fd,z])
        vr.append([       mx,drn+fd,z]);vr.append([ mx+k1-fd,drn+fd,z]);vr.append([mx+k1-fd,     0,z])
        n=len(vr)
        fc.append([n- 1,n- 2,n- 8,n- 7]);fc.append([n- 3,n- 9,n- 8,n- 2]);fc.append([n- 2,n- 1,n-13,n-14])
        fc.append([n- 3,n- 2,n-14,n-15]);fc.append([n-15,n-14,n-20,n-21]);fc.append([n-14,n-13,n-19,n-20])
        fc.append([n- 4,n- 5,n-11,n-10]);fc.append([n- 5,n- 6,n-12,n-11]);fc.append([n- 5,n- 4,n-16,n-17])
        fc.append([n- 6,n- 5,n-17,n-18]);fc.append([n-24,n-18,n-17,n-23]);fc.append([n-23,n-17,n-16,n-22])
        if self.fg>1:
            if self.fg%2==0:
                if i < self.fg/2:fc.append([7,n-16,n-4]);fc.append([6,n-3,n-15])
                if i+1<self.fg/2:fc.append([7,n- 4,n+8]);fc.append([6,n+9,n- 3])
                if i+1>self.fg/2:fc.append([4,n-16,n-4]);fc.append([5,n-3,n-15])
                if i+1>self.fg/2 and i+1<self.fg:fc.append([4,n-4,n+8]);fc.append([5,n+9,n-3])
            else:
                if i<self.fg//2:
                    fc.append([7,n-16,n-4]);fc.append([6,n-3,n-15])
                    fc.append([7,n- 4,n+8]);fc.append([6,n+9,n- 3])
                if i > self.fg//2:fc.append([4,n-16,n-4]);fc.append([5,n-3,n-15])
                if i+1>self.fg//2 and i+1<self.fg:fc.append([4,n- 4,n+8]);fc.append([5,n+9,n-3])
        if i<self.fg-1 and self.fg>1:
            fc.append([n- 7,n- 8,n+4,n+5]);fc.append([n- 8,n- 9,n+3,n+4]);fc.append([n-9,n- 3,n+9,n+3])
            fc.append([n-10,n-11,n+1,n+2]);fc.append([n-11,n-12, n ,n+1]);fc.append([n-4,n-10,n+2,n+8])
        if i==self.fg-1:
            fc.append([0, 8,n-11,n-12]);fc.append([ 8,12,n-10,n-11]);fc.append([12,4,n-4,n-10])
            fc.append([5,13,n- 9,n- 3]);fc.append([13, 9,n- 8,n- 9]);fc.append([ 9,1,n-7,n- 8])
    SM=[]
    #Duz----------------
    if self.dr==False:
        fc.append([14,10,11,15]);fc.append([6,14,15,7])
    #Yuvarlak-----------
    else:
        if dh>mx:dh=mx;self.dh=mx*100
        vr[ 6][2]-=dh;vr[ 7][2]-=dh
        vr[14][2]-=dh;vr[15][2]-=dh
        O=mx/dh
        H1=sqrt(mx**2+dh**2)/2
        H2=H1*O
        R=sqrt(H1**2+H2**2)
        M=ust-R
        A=pi-atan(O)*2
        for a in range(1,24):
            p=(a*A/12)+(pi*1.5)-A
            vr.append([cos(p)*R,pdr,M-sin(p)*R])
            vr.append([cos(p)*R,drn,M-sin(p)*R])
            n=len(vr)
            if a==1:
                fc.append([n-1,15,7,n-2])
                SM.append(len(fc))
                fc.append([15,n-1,11])
            elif a<23:
                fc.append([n-1,n-3,n-4,n-2])
                SM.append(len(fc))
                if a<13:   fc.append([n-3,n-1,11])
                elif a==13:fc.append([n-3,n-1,10,11])
                else:      fc.append([n-3,n-1,10])
            elif a==23:
                fc.append([n-1,n-3,n-4,n-2])
                SM.append(len(fc))
                fc.append([n-3,n-1,10])
                fc.append([14,n-1,n-2,6])
                SM.append(len(fc))
                fc.append([n-1,14,10])
#OBJE -----------------------------------------------------------
    mesh = bpy.data.meshes.new(name='Sove')
    bpy.data.objects.new('Sove', mesh)
    mesh.from_pydata(vr,[],fc)
 #   for i in SM:
 #       mesh.faces[i-1].shade_smooth()
    mesh.materials.append(MSVE())
    mesh.update(calc_edges=True)
    object_data_add(context, mesh, operator=None)
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
#----------------------------------------------------------------
class OBJECT_OT_add_object(bpy.types.Operator):
    bl_idname = "mesh.add_say3d_sove"
    bl_label = "Sove"
    bl_description = "Sove Frame"
    bl_options = {'REGISTER', 'UNDO'}

    prs = EnumProperty(items = (("1","PENCERE 200",""),
                                ("2","PENCERE 180",""),
                                ("3","PENCERE 160","")),
                                name="",description="")
    son=prs
    gen=IntProperty(name='Width', min=1,max= 400,default=200,description='Width')
    knr=IntProperty(name='Thickness', min=1,max= 100,default= 15,description='Thickness')
    yuk=IntProperty(name='Elevation',min=1,max=3000,default=590,description='Elevation')
    alt=IntProperty(name='Old Spacing',      min=1,max= 300,default= 44,description='Old Spacing')
    ust=IntProperty(name='Top margin',      min=1,max= 300,default= 33,description='Top margin')
    sdr=IntProperty(name='Jamb', min=1,max= 100,default= 15,description='jamb Depth')
    pdr=IntProperty(name='Wall Thickness',    min=0,max= 100,default= 20,description='Wall Thickness')
    dh =IntProperty(name='',         min=1,max= 200,default= 30,description='Height')
    dr=BoolProperty(name='Rounded', default=True,  description='Rounded')

    fg =IntProperty(name='Gap',min=0,max=10,default=1,description='Gap')
    fh =IntProperty(name='',    min=1,max=10,default=3,description='Height')
    fd =IntProperty(name='',    min=1,max=10,default=2,description='Depth')

    f0 =IntProperty(name='Interval',min=1,max=3000,default=90,description='Interval')
    f1 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f2 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f3 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f4 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f5 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f6 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f7 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f8 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    f9 =IntProperty(name='Interval',min=1,max=3000,default=30,description='Interval')
    #--------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        layout.prop(self,'prs')
        box=layout.box()
        box.prop(self,'gen');box.prop(self,'yuk')
        box.prop(self,'knr')
        row=box.row();row.prop(self,'alt');row.prop(self,'ust')
        row=box.row();row.prop(self,'sdr');row.prop(self,'pdr')
        row=box.row();row.prop(self, 'dr');row.prop(self, 'dh')
        box=layout.box()
        box.prop(self,'fg')
        row=box.row();row.prop(self, 'fh');row.prop(self, 'fd')
        for i in range(self.fg):
            box.prop(self,'f'+str(i))

    def execute(self, context):
        if self.son!=self.prs:
            if self.prs=='1':Prs(self,200,15,590,44,33,15,20,30,True,1,2,3,90,30,30,30,30,30,30,30,30,30)
            if self.prs=='2':Prs(self,180,15,590,44,33,15,20,30,True,1,2,3,90,30,30,30,30,30,30,30,30,30)
            if self.prs=='3':Prs(self,160,15,590,44,33,15,20,30,True,1,2,3,90,30,30,30,30,30,30,30,30,30)
            self.son=self.prs
        add_object(self, context)
        return {'FINISHED'}
