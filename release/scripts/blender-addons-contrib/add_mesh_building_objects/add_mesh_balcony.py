'''
bl_info = {
    "name": "Balcony",
    "author": "SayPRODUCTIONS",
    "version": (1, 0),
    "blender": (2, 59, 0),
    "location": "View3D > Add > Mesh > Say3D",
    "description": "Balcony olusturma",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}
'''
import bpy, bmesh
from bpy.props import *
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
import operator
import os
from math import pi, sin, cos, sqrt, atan
def MAT(AD,R,G,B):
    if AD not in bpy.data.materials:
        mtl=bpy.data.materials.new(AD)
        mtl.diffuse_color     = ([R,G,B])
        mtl.diffuse_shader    = 'LAMBERT'
        mtl.diffuse_intensity = 1.0
    else:
        mtl=bpy.data.materials[AD]
    return mtl
def Prs(s,v):
    if v=='1':
        s.lst=3
        s.ls0='1';s.by0= 80;s.bk0=20;s.bf0=4;s.fh0=3;s.fd0=2;s.f00=16;s.f01=12;s.f02=12;s.f03=12
        s.ls1='3';s.my1=  4;s.mg1= 4
        s.ls2='4';s.kt2="2";s.ky2= 5;s.kk2=5
    if v=='2':
        s.lst=5
        s.ls0='1';s.by0= 15;s.bk0=20;s.bf0=0
        s.ls1='2';s.py1= 60;s.pd1=10
        s.ls2='1';s.by2= 15;s.bk2=20;s.bf2=0
        s.ls3='3';s.my3=  4;s.mg3= 4
        s.ls4='4';s.kt4="2";s.ky4= 5;s.kk4=5
    if v=='3':
        s.lst=3
        s.ls0='1';s.by0= 40;s.bk0=10;s.bf0=0
        s.ls1='5';s.cy1= 56
        s.ls2='4';s.kt2="1";s.ky2= 0;s.kk2=4
    if v=='4':
        s.lst=2
        s.ls0='1';s.by0= 30;s.bk0=20;s.bf0=0
        s.ls1='3';s.my1=  4;s.mg1= 4
    if v=='5':
        s.lst=2
        s.ls0='1';s.by0= 27;s.bk0=20;s.bf0=2;s.fh0=3;s.fd0=2;s.f00=7;s.f01=7
        s.ls1='3';s.my1=  4;s.mg1= 4
    if v=='6':
        s.lst=6
        s.ls0='1';s.by0= 50;s.bk0=20;s.bf0=2;s.fh0=3;s.fd0=2;s.f00=12;s.f01=20
        s.ls1='3';s.my1=  4;s.mg1= 4
        s.ls2='4';s.kt2="2";s.ky2= 5;s.kk2=4
        s.ls3='4';s.kt3="2";s.ky3= 5;s.kk3=4
        s.ls4='4';s.kt4="2";s.ky4= 5;s.kk4=4
        s.ls5='4';s.kt5="2";s.ky5= 5;s.kk5=5
def EXT(PR,vr,fc,lz,mz,rz):
    n=len(vr)
    m=len(PR)
    if lz==0:
        for P in PR:vr.append([-mz,P[0],P[1]])
    else:
        for P in PR:vr.append([ P[0]-mz,  lz,P[1]])
        for P in PR:vr.append([ P[0]-mz,P[0],P[1]])
    if rz==0:
        for P in PR:vr.append([ mz,P[0],P[1]])
    else:
        for P in PR:vr.append([-P[0]+mz,P[0],P[1]])
        for P in PR:vr.append([-P[0]+mz,  rz,P[1]])
    if   lz==0 and rz==0:l=1
    elif lz==0 and rz> 0:l=2
    elif lz> 0 and rz==0:l=2
    elif lz> 0 and rz> 0:l=3
    for j in range(0,l):
        for i in range(0,m):
            a=j*m
            if i==m-1:fc.append([a+i+n,a+0+n+0,a+0+n+0+m,a+i+n+m])
            else:     fc.append([a+i+n,a+i+n+1,a+i+n+1+m,a+i+n+m])
def add_object(s,context):
    fc=[];vr=[];SM=[]
    Bal=[];Par=[];Mer=[];Krm=[];Glass=[];Dos=[]
    blok=[]#    [ Tip ][             Balcony           [                    Joint_Gap                        ] [  Bulwark  ] [   Marble  ] [       Chrome      ] [  Glass  ]
    blok.append([s.ls0,[s.by0,s.bk0,s.bf0,s.fh0,s.fd0,[s.f00,s.f01,s.f02,s.f03,s.f04,s.f05,s.f06,s.f07]],[s.py0,s.pd0],[s.my0,s.mg0],[s.kt0,s.ky0,s.kk0],[s.cy0]])
    blok.append([s.ls1,[s.by1,s.bk1,s.bf1,s.fh1,s.fd1,[s.f10,s.f11,s.f12,s.f13,s.f14,s.f15,s.f16,s.f17]],[s.py1,s.pd1],[s.my1,s.mg1],[s.kt1,s.ky1,s.kk1],[s.cy1]])
    blok.append([s.ls2,[s.by2,s.bk2,s.bf2,s.fh2,s.fd2,[s.f20,s.f21,s.f22,s.f23,s.f24,s.f25,s.f26,s.f27]],[s.py2,s.pd2],[s.my2,s.mg2],[s.kt2,s.ky2,s.kk2],[s.cy2]])
    blok.append([s.ls3,[s.by3,s.bk3,s.bf3,s.fh3,s.fd3,[s.f30,s.f31,s.f32,s.f33,s.f34,s.f35,s.f36,s.f37]],[s.py3,s.pd3],[s.my3,s.mg3],[s.kt3,s.ky3,s.kk3],[s.cy3]])
    blok.append([s.ls4,[s.by4,s.bk4,s.bf4,s.fh4,s.fd4,[s.f40,s.f41,s.f42,s.f43,s.f44,s.f45,s.f46,s.f47]],[s.py4,s.pd4],[s.my4,s.mg4],[s.kt4,s.ky4,s.kk4],[s.cy4]])
    blok.append([s.ls5,[s.by5,s.bk5,s.bf5,s.fh5,s.fd5,[s.f50,s.f51,s.f52,s.f53,s.f54,s.f55,s.f56,s.f57]],[s.py5,s.pd5],[s.my5,s.mg5],[s.kt5,s.ky5,s.kk5],[s.cy5]])
    blok.append([s.ls6,[s.by6,s.bk6,s.bf6,s.fh6,s.fd6,[s.f60,s.f61,s.f62,s.f63,s.f64,s.f65,s.f66,s.f67]],[s.py6,s.pd6],[s.my6,s.mg6],[s.kt6,s.ky6,s.kk6],[s.cy6]])
    blok.append([s.ls7,[s.by7,s.bk7,s.bf7,s.fh7,s.fd7,[s.f70,s.f71,s.f72,s.f73,s.f74,s.f75,s.f76,s.f77]],[s.py7,s.pd7],[s.my7,s.mg7],[s.kt7,s.ky7,s.kk7],[s.cy7]])

    h=-s.dds/100;dh=h+s.dhg/100;du=s.duz/100;
    lz=s.luz/100;mz=s.muz/200;rz=s.ruz/100
    dg=-((blok[0][1][1]-s.ddg)/100)
    if h<0:#Pavement
        if lz==0 and rz==0:
            vr=[[-mz,du,h],[ mz,du, h],[-mz,dg, h],[ mz,dg, h],[-mz,dg, 0],
                [ mz,dg,0],[-mz, 0,dh],[ mz, 0,dh],[-mz,du,dh],[ mz,du,dh]]
            fc=[[0,1,3,2],[2,3,5,4],[6,7,9,8]];Dos=[0,1,2]
        if lz==0 and rz >0:
            vr=[[-mz,   du,h],[ mz-dg,du, h],[-mz,   dg, h],[ mz-dg,dg, h],[-mz,   dg, 0],
                [ mz-dg,dg,0],[-mz, 0,   dh],[ mz-dg, 0,dh],[-mz,   du,dh],[ mz-dg,du,dh],[ mz-dg,du,0]]
            fc=[[0,1,3,2],[2,3,5,4],[6,7,9,8],[3,1,10,5]];Dos=[0,1,2,3]
        if lz >0 and rz==0:
            vr=[[-mz+dg,du,h],[ mz,   du, h],[-mz+dg,dg, h],[ mz,   dg, h],[-mz+dg,dg, 0],
                [ mz,   dg,0],[-mz+dg, 0,dh],[ mz,    0,dh],[-mz+dg,du,dh],[ mz,   du,dh],[-mz+dg,du,0]]
            fc=[[0,1,3,2],[2,3,5,4],[6,7,9,8],[0,2,4,10]];Dos=[0,1,2,3]
        if lz >0 and rz >0:
            vr=[[-mz+dg,dg,0],[mz-dg,dg,0],[-mz+dg,dg, h],[mz-dg,dg, h],[-mz+dg,du, h],[mz-dg,du, h],
                [-mz+dg,du,0],[mz-dg,du,0],[-mz,    0,dh],[mz,    0,dh],[-mz,   du,dh],[mz,   du,dh]]
            fc=[[1,0,2,3],[3,2,4,5],[6,4,2,0],[3,5,7,1],[8,9,11,10]];Dos=[0,1,2,3,4]
    else:
        vr=[[-mz, 0, h],[mz, 0, h],[-mz,du, h],[mz,du, h],
            [-mz,du,dh],[mz,du,dh],[-mz, 0,dh],[mz, 0,dh]]
        fc=[[1,0,2,3],[5,4,6,7]];Dos=[0,1]
    z=0
    for i in range(s.lst):
        if blok[i][0]=='1':#Balcony
            k1=blok[i][1][1]/100;h =blok[i][1][0]/100
            fh=blok[i][1][3]/100;fd=blok[i][1][4]/100
            PR=[[-k1,z],[0,z],[0,z+h],[-k1,z+h]]
            z+=h;fz=z
            for f in range(blok[i][1][2]):
                fz-=blok[i][1][5][f]/100
                PR.append([-k1,   fz   ]);PR.append([-k1+fd,fz   ])
                PR.append([-k1+fd,fz-fh]);PR.append([-k1,   fz-fh])
                fz-=fh
            BB=len(fc)
            EXT(PR,vr,fc,lz,mz,rz)
            BE=len(fc)
            for F in range(BB,BE):Bal.append(F)
        if blok[i][0]=='2':#Bulwark
            k1=blok[i][2][1]/100;h=blok[i][2][0]/100
            PR=[[-k1,z],[0,z],[0,z+h],[-k1,z+h]]
            z+=h
            BB=len(fc)
            EXT(PR,vr,fc,lz,mz,rz)
            BE=len(fc)
            for F in range(BB,BE):Par.append(F)
        if blok[i][0]=='3':#Marble
            k1=blok[0][1][1]/100;k2=blok[i][3][1]/100;h=blok[i][3][0]/100
            PR=[[-k1-k2,z],[k2,z],[k2,z+h],[-k1-k2,z+h]]
            z+=h
            BB=len(fc)
            EXT(PR,vr,fc,lz,mz,rz)
            BE=len(fc)
            for F in range(BB,BE):Mer.append(F)
        if blok[i][0]=='4':#Chrome
            k1=blok[0][1][1]/200;k2=blok[i][4][2]/200;h=blok[i][4][1]/100
            if blok[i][4][0]=="1":#Duz
                z+=h
                PR=[[-k1-k2,z],[-k1+k2,z],[-k1+k2,z+k2*2],[-k1-k2,z+k2*2]]
                z+=k2*2
            else:#Round
                PR=[];z+=h+k2
                for a in range(24):
                    x=-k1+cos(a*pi/12)*k2;y=z+sin(a*pi/12)*k2
                    PR.append([x,y])
                z+=k2
            BB=len(fc)
            EXT(PR,vr,fc,lz,mz,rz)
            BE=len(fc)
            for F in range(BB,BE):Krm.append(F)
            if blok[i][4][0]=="2":
                for F in range(BB,BE):SM.append(F)
        if blok[i][0]=='5':#Glass
            k1=blok[0][1][1]/200;h=blok[i][5][0]/100
            PR=[[-k1-0.001,z],[-k1+0.001,z],[-k1+0.001,z+h],[-k1-0.001,z+h]]
            z+=h;BB=len(fc);n=len(vr)
            fc.append([n+1,n,n+3,n+2])
            EXT(PR,vr,fc,lz,mz,rz)
            n=len(vr)
            fc.append([n-2,n-1,n-4,n-3])
            BE=len(fc)
            for F in range(BB,BE):Glass.append(F)
#OBJE -----------------------------------------------------------
    mesh = bpy.data.meshes.new(name='Balcony')
    mesh.from_pydata(vr,[],fc)
    for i in SM:
        mesh.polygons[i].use_smooth = 1
    mesh.materials.append(MAT('Balcony', 0.66,0.64,0.72))
    mesh.materials.append(MAT('Bulwark',0.46,0.44,0.52))
    mesh.materials.append(MAT('Marble', 0.90,0.85,0.80))
    mesh.materials.append(MAT('Chrome',   0.50,0.55,0.60))
    mesh.materials.append(MAT('Glass',    0.50,0.80,1.00))
    mesh.materials.append(MAT('Pavement', 1.00,1.00,1.00))

    for i in Bal:mesh.polygons[i].material_index = 0
    for i in Par:mesh.polygons[i].material_index = 1
    for i in Mer:mesh.polygons[i].material_index = 2
    for i in Krm:mesh.polygons[i].material_index = 3
    for i in Glass:mesh.polygons[i].material_index = 4
    for i in Dos:mesh.polygons[i].material_index = 5

    mesh.update(calc_edges=True)
    object_data_add(context, mesh, operator=None)
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
#----------------------------------------------------------------
class OBJECT_OT_add_balcony(bpy.types.Operator):
    bl_idname = "mesh.add_say3d_balcony"
    bl_label = "Balcony"
    bl_description = "Balcony Olustur"
    bl_options = {'REGISTER', 'UNDO'}
    prs = EnumProperty(items = (("1","Joint_Gap",    ""),
                                ("2","Bulwark", ""),
                                ("3","Glass",     ""),
                                ("4","Marquise",  ""),
                                ("5","Eaves",   ""),
                                ("6","Railing","")))
    son=prs
    lst=IntProperty(         min=1,max=   8,default=  3)
    luz=IntProperty(name='<',min=0,max=1000,default=100)
    muz=IntProperty(         min=0,max=1000,default=200)
    ruz=IntProperty(name='>',min=0,max=1000,default=100)

    duz=IntProperty(min=  1,max=500,default=100,description="Pavement Width")
    dhg=IntProperty(min=  1,max= 50,default= 17,description="Pavement Height")
    dds=IntProperty(min=-50,max= 50,default= 10,description="Pavement Height")
    ddg=IntProperty(min=  0,max= 50,default= 10,description="Pavement Width")
    #Tip
    ls0=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="1")
    #Balcony
    by0=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk0=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf0=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 4,description='Joint_Gap'     )
    fh0=IntProperty(min=1,max= 10,default= 3);fd0=IntProperty(min=1,max= 10,default= 2)
    f00=IntProperty(min=1,max=200,default=16);f01=IntProperty(min=1,max=200,default=12)
    f02=IntProperty(min=1,max=200,default=12);f03=IntProperty(min=1,max=200,default=12)
    f04=IntProperty(min=1,max=200,default= 3);f05=IntProperty(min=1,max=200,default= 3)
    f06=IntProperty(min=1,max=200,default= 3);f07=IntProperty(min=1,max=200,default= 3)
    #Bulwark
    py0=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd0=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my0=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg0=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt0=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky0=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk0=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy0=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls1=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="3")
    #Balcony
    by1=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk1=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf1=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh1=IntProperty(min=1,max= 10,default=3);fd1=IntProperty(min=1,max= 10,default=2)
    f10=IntProperty(min=1,max=200,default=3);f11=IntProperty(min=1,max=200,default=3)
    f12=IntProperty(min=1,max=200,default=3);f13=IntProperty(min=1,max=200,default=3)
    f14=IntProperty(min=1,max=200,default=3);f15=IntProperty(min=1,max=200,default=3)
    f16=IntProperty(min=1,max=200,default=3);f17=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py1=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd1=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my1=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg1=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt1=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky1=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk1=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy1=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls2=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="4")
    #Balcony
    by2=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk2=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf2=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh2=IntProperty(min=1,max= 10,default=3);fd2=IntProperty(min=1,max= 10,default=2)
    f20=IntProperty(min=1,max=200,default=3);f21=IntProperty(min=1,max=200,default=3)
    f22=IntProperty(min=1,max=200,default=3);f23=IntProperty(min=1,max=200,default=3)
    f24=IntProperty(min=1,max=200,default=3);f25=IntProperty(min=1,max=200,default=3)
    f26=IntProperty(min=1,max=200,default=3);f27=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py2=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd2=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my2=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg2=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt2=EnumProperty(items=(("1","Square",""),("2","Round","")),default="2")
    ky2=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk2=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy2=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls3=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="4")
    #Balcony
    by3=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk3=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf3=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh3=IntProperty(min=1,max= 10,default=3);fd3=IntProperty(min=1,max= 10,default=2)
    f30=IntProperty(min=1,max=200,default=3);f31=IntProperty(min=1,max=200,default=3)
    f32=IntProperty(min=1,max=200,default=3);f33=IntProperty(min=1,max=200,default=3)
    f34=IntProperty(min=1,max=200,default=3);f35=IntProperty(min=1,max=200,default=3)
    f36=IntProperty(min=1,max=200,default=3);f37=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py3=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd3=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my3=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg3=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt3=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky3=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk3=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy3=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls4=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="4")
    #Balcony
    by4=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk4=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf4=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh4=IntProperty(min=1,max= 10,default=3);fd4=IntProperty(min=1,max= 10,default=2)
    f40=IntProperty(min=1,max=200,default=3);f41=IntProperty(min=1,max=200,default=3)
    f42=IntProperty(min=1,max=200,default=3);f43=IntProperty(min=1,max=200,default=3)
    f44=IntProperty(min=1,max=200,default=3);f45=IntProperty(min=1,max=200,default=3)
    f46=IntProperty(min=1,max=200,default=3);f47=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py4=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd4=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my4=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg4=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt4=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky4=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk4=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy4=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls5=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="4")
    #Balcony
    by5=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk5=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf5=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh5=IntProperty(min=1,max= 10,default=3);fd5=IntProperty(min=1,max= 10,default=2)
    f50=IntProperty(min=1,max=200,default=3);f51=IntProperty(min=1,max=200,default=3)
    f52=IntProperty(min=1,max=200,default=3);f53=IntProperty(min=1,max=200,default=3)
    f54=IntProperty(min=1,max=200,default=3);f55=IntProperty(min=1,max=200,default=3)
    f56=IntProperty(min=1,max=200,default=3);f57=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py5=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd5=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my5=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg5=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt5=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky5=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk5=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy5=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls6=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="4")
    #Balcony
    by6=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk6=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf6=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh6=IntProperty(min=1,max= 10,default=3);fd6=IntProperty(min=1,max= 10,default=2)
    f60=IntProperty(min=1,max=200,default=3);f61=IntProperty(min=1,max=200,default=3)
    f62=IntProperty(min=1,max=200,default=3);f63=IntProperty(min=1,max=200,default=3)
    f64=IntProperty(min=1,max=200,default=3);f65=IntProperty(min=1,max=200,default=3)
    f66=IntProperty(min=1,max=200,default=3);f67=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py6=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd6=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my6=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg6=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt6=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky6=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk6=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy6=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    #Tip
    ls7=EnumProperty(items=(("1","Balcony",""),("2","Bulwark",""),("3","Marble",""),("4","Chrome",""),("5","Glass","")),default="4")
    #Balcony
    by7=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    bk7=IntProperty(name='Thickness', min=1,max= 50,default=20,description='Thickness' )
    bf7=IntProperty(name='Joint_Gap',     min=0,max=  8,default= 0,description='Joint_Gap'     )
    fh7=IntProperty(min=1,max= 10,default=3);fd7=IntProperty(min=1,max= 10,default=2)
    f70=IntProperty(min=1,max=200,default=3);f71=IntProperty(min=1,max=200,default=3)
    f72=IntProperty(min=1,max=200,default=3);f73=IntProperty(min=1,max=200,default=3)
    f74=IntProperty(min=1,max=200,default=3);f75=IntProperty(min=1,max=200,default=3)
    f76=IntProperty(min=1,max=200,default=3);f77=IntProperty(min=1,max=200,default=3)
    #Bulwark
    py7=IntProperty(name='Elevation',min=1,max=200,default=80,description='Elevation')
    pd7=IntProperty(name='Thickness', min=1,max= 50,default=10,description='Thickness' )
    #Marble
    my7=IntProperty(name='Elevation',min=1,max=50,default=4,description='Elevation')
    mg7=IntProperty(name='maxWidth', min=0,max=20,default=4,description='maxWidth' )
    #Chrome
    kt7=EnumProperty(items=(("1","Square",""),("2","Round","")))
    ky7=IntProperty(min=0,max=50,default=5,description='CutOut'  )
    kk7=IntProperty(min=1,max=20,default=5,description='Thickness')
    #Glass
    cy7=IntProperty(name='Elevation',min=1,max=100,default=20,description='Elevation')
    #--------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        layout.prop(self,'prs', text="Wall Style")
        layout.prop(self,'lst', text="Add Level")
        row=layout.row()
        row.label(text="Wall Length & Width")
        row=layout.row()
        row.prop(self,'luz')
        row.prop(self,'muz')
        row.prop(self,'ruz')

        layout.label('Pavement XYZ')
        row=layout.row();row.prop(self,'duz');row.prop(self,'dhg')
        row=layout.row();row.prop(self,'dds');row.prop(self,'ddg')

        ls=[];lf=[]
        ls.append(self.ls0);lf.append(self.bf0)
        ls.append(self.ls1);lf.append(self.bf1)
        ls.append(self.ls2);lf.append(self.bf2)
        ls.append(self.ls3);lf.append(self.bf3)
        ls.append(self.ls4);lf.append(self.bf4)
        ls.append(self.ls5);lf.append(self.bf5)
        ls.append(self.ls6);lf.append(self.bf6)
        ls.append(self.ls7);lf.append(self.bf7)
        for i in range(self.lst-1,-1,-1):
            box=layout.box()
            box.prop(self,'ls'+str(i))
            if  ls[i]=='1':#Balcony
                box.prop(self,'by'+str(i))
                box.prop(self,'bk'+str(i))
                box.prop(self,'bf'+str(i))
                if lf[i]>0:
                    row=box.row()
                    row.prop(self,'fh'+str(i))
                    row.prop(self,'fd'+str(i))
                for f in range(lf[i]):
                    box.prop(self,'f'+str(i)+str(f))
            if  ls[i]=='2':#Bulwark
                box.prop(self,'py'+str(i))
                box.prop(self,'pd'+str(i))
            if  ls[i]=='3':#Marble
                row=box.row()
                row.prop(self,'my'+str(i))
                row.prop(self,'mg'+str(i))
            if  ls[i]=='4':#Chrome
                row=box.row()
                row.prop(self,'kt'+str(i))
                row.prop(self,'ky'+str(i))
                row.prop(self,'kk'+str(i))
            if  ls[i]=='5':#Glass
                box.prop(self,'cy'+str(i))
    def execute(self, context):
        if self.son!=self.prs:
            Prs(self,self.prs)
            self.son=self.prs
        add_object(self,context)
        return {'FINISHED'}
# Registration
def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_balcony.bl_idname,
        text="Balcony",
        icon="SNAP_FACE")
def register():
    bpy.utils.register_class(OBJECT_OT_add_balcony)
    bpy.types.INFO_MT_mesh_add.append(add_object_button)
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_balcony)
    bpy.types.INFO_MT_mesh_add.remove(add_object_button)
if __name__ == '__main__':
    register()