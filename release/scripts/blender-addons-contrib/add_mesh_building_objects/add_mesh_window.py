'''bl_info = {
    "name": "Window Generator 2",
    "author": "SayPRODUCTIONS",
    "version": (2, 0),
    "blender": (2, 63, 0),
    "location": "View3D > Add > Mesh > Say3D",
    "description": "Window Generator 2",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}
	'''
import bpy
from bpy.props import *
from math import pi, sin, cos, sqrt, radians
def MAT(AD,R,G,B):
    if AD not in bpy.data.materials:
        mtl=bpy.data.materials.new(AD)
        mtl.diffuse_color     = ([R,G,B])
        mtl.diffuse_shader    = 'LAMBERT'
        mtl.diffuse_intensity = 1.0
    else:
        mtl=bpy.data.materials[AD]
    return mtl
def Fitil(vr,fc,X,Z,x,y,z,zz,xx):
    k3=z*2
    vr.extend([[X[x  ]+xx,-z+zz,Z[y  ]+xx],[X[x  ]+xx+k3,-z+zz,Z[y  ]+xx+k3],[X[x  ]+xx+k3,z+zz,Z[y  ]+xx+k3],[X[x  ]+xx,z+zz,Z[y  ]+xx]])
    vr.extend([[X[x  ]+xx,-z+zz,Z[y+1]-xx],[X[x  ]+xx+k3,-z+zz,Z[y+1]-xx-k3],[X[x  ]+xx+k3,z+zz,Z[y+1]-xx-k3],[X[x  ]+xx,z+zz,Z[y+1]-xx]])
    vr.extend([[X[x+1]-xx,-z+zz,Z[y+1]-xx],[X[x+1]-xx-k3,-z+zz,Z[y+1]-xx-k3],[X[x+1]-xx-k3,z+zz,Z[y+1]-xx-k3],[X[x+1]-xx,z+zz,Z[y+1]-xx]])
    vr.extend([[X[x+1]-xx,-z+zz,Z[y  ]+xx],[X[x+1]-xx-k3,-z+zz,Z[y  ]+xx+k3],[X[x+1]-xx-k3,z+zz,Z[y  ]+xx+k3],[X[x+1]-xx,z+zz,Z[y  ]+xx]])
    n=len(vr)
    fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10]])
    fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6]])
    fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2]])
    fc.extend([[n- 4,n- 3,n-15,n-16],[n- 3,n- 2,n-14,n-15],[n- 2,n- 1,n-13,n-14]])
    z=0.005
    vr.extend([[X[x]+xx+k3,-z+zz,Z[y]+xx+k3],[X[x]+xx+k3,-z+zz,Z[y+1]-xx-k3],[X[x+1]-xx-k3,-z+zz,Z[y+1]-xx-k3],[X[x+1]-xx-k3,-z+zz,Z[y]+xx+k3]])
    vr.extend([[X[x]+xx+k3, z+zz,Z[y]+xx+k3],[X[x]+xx+k3, z+zz,Z[y+1]-xx-k3],[X[x+1]-xx-k3, z+zz,Z[y+1]-xx-k3],[X[x+1]-xx-k3, z+zz,Z[y]+xx+k3]])
    fc.extend([[n+1,n+0,n+3,n+2],[n+4,n+5,n+6,n+7]])
def Kapak(vr,fc,X,Z,x,y,z,zz):
    k2=z*2
    vr.extend([[X[x  ],-z+zz,Z[y  ]],[X[x  ]+k2,-z+zz,Z[y  ]+k2],[X[x  ]+k2,z+zz,Z[y  ]+k2],[X[x  ],z+zz,Z[y  ]]])
    vr.extend([[X[x  ],-z+zz,Z[y+1]],[X[x  ]+k2,-z+zz,Z[y+1]-k2],[X[x  ]+k2,z+zz,Z[y+1]-k2],[X[x  ],z+zz,Z[y+1]]])
    vr.extend([[X[x+1],-z+zz,Z[y+1]],[X[x+1]-k2,-z+zz,Z[y+1]-k2],[X[x+1]-k2,z+zz,Z[y+1]-k2],[X[x+1],z+zz,Z[y+1]]])
    vr.extend([[X[x+1],-z+zz,Z[y  ]],[X[x+1]-k2,-z+zz,Z[y  ]+k2],[X[x+1]-k2,z+zz,Z[y  ]+k2],[X[x+1],z+zz,Z[y  ]]])
    n=len(vr)
    fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10],[n-13,n-16,n-12,n- 9]])
    fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6],[n- 9,n-12,n- 8,n- 5]])
    fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2],[n- 5,n- 8,n- 4,n- 1]])
    fc.extend([[n- 4,n- 3,n-15,n-16],[n- 3,n- 2,n-14,n-15],[n- 2,n- 1,n-13,n-14],[n- 1,n- 4,n-16,n-13]])
def Prs(s):
    if  s.prs=='1':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=190;s.mr=True
        s.gnx0=  60;s.gnx1=  110;s.gnx2=  60
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='2':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=190;s.mr=True
        s.gnx0=  60;s.gnx1=   60;s.gnx2=  60
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='3':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=190;s.mr=True
        s.gnx0=  55;s.gnx1=   50;s.gnx2=  55
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='4':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=150;s.mr=True
        s.gnx0=  55;s.gnx1=   50;s.gnx2=  55
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='5':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=150;s.mr=True
        s.gnx0=  50;s.gnx1=   40;s.gnx2=  50
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='6':
        s.gen=1;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=40;s.mr=True
        s.gnx0=40
        s.k00 =False
    if  s.prs=='7':
        s.gen=1;s.yuk=2;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=195;s.gny1=40
        s.gnx0=70
        s.k00 =True;s.k10 =False
        s.mr=False
    if  s.prs=='8':
        s.gen=1;s.yuk=2;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=180;s.gny1=35
        s.gnx0=70
        s.k00 =True;s.k10 =False
        s.mr=False
def add_object(self, context):
    fc=[];vr=[];kx=[]
    mx=self.gen;my=self.yuk;k1=self.kl1/100;y=my*4+4;k2=self.kl2/100;k3=self.fk/200;fr=(k1+k2)*0.5-0.01
    RES=self.RES

    u=self.kl1/100;X=[0,round(u,2)]
    if mx> 0:u+=self.gnx0 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 1:u+=self.gnx1 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 2:u+=self.gnx2 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 3:u+=self.gnx3 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 4:u+=self.gnx4 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 5:u+=self.gnx5 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 6:u+=self.gnx6 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 7:u+=self.gnx7 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    X[-1]=X[-2]+k1

    u=self.kl1/100;Z=[0,round(u,2)]
    if my> 0:u+=self.gny0 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 1:u+=self.gny1 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 2:u+=self.gny2 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 3:u+=self.gny3 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 4:u+=self.gny4 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    Z[-1]=Z[-2]+k1

    u = X[-1]/2
    for i in range(0,len(X)):X[i]-=u
    kx=[[self.k00,self.k10,self.k20,self.k30,self.k40],
        [self.k01,self.k11,self.k21,self.k31,self.k41],
        [self.k02,self.k12,self.k22,self.k32,self.k42],
        [self.k03,self.k13,self.k23,self.k33,self.k43],
        [self.k04,self.k14,self.k24,self.k34,self.k44],
        [self.k05,self.k15,self.k25,self.k35,self.k45],
        [self.k06,self.k16,self.k26,self.k36,self.k46],
        [self.k07,self.k17,self.k27,self.k37,self.k47]]
    cam=[];mer=[];ftl=[];SM=[]
#VERTICES ------------------------
    vr.extend([[X[0],-k1/2,Z[0]],[X[0],k1/2,Z[0]]])
    for x in range(1,len(X)-1):vr.extend([[X[x],-k1/2,Z[1]],[X[x], k1/2,Z[1]]])
    vr.extend([[X[-1],-k1/2,Z[0]],[X[-1], k1/2,Z[0]]])
    for z in range(2,len(Z)-2,2):
        for x in range(0,len(X)):vr.extend([[X[x],-k1/2,Z[z]],[X[x], k1/2,Z[z]]])
        for x in range(0,len(X)):vr.extend([[X[x],-k1/2,Z[z+1]],[X[x], k1/2,Z[z+1]]])
    z=len(Z)-2
    vr.extend([[X[0],-k1/2,Z[z+1]],[X[0], k1/2,Z[z+1]]])
    ALT=[];UST=[len(vr)-2,len(vr)-1]
    for x in range(1,len(X)-1):
        vr.extend([[X[x],-k1/2,Z[z]],[X[x], k1/2,Z[z]]])
        ALT.extend([len(vr)-2,len(vr)-1])
    vr.extend([[X[-1],-k1/2,Z[z+1]],[X[-1],k1/2,Z[z+1]]])
    SON=[len(vr)-2,len(vr)-1]
#FACES ---------------------------
    fc.append([0,1,3+mx*4,2+mx*4])
    FB=[0];FR=[1]
    for i in range(0,mx*4,4):
        fc.append([i+3,i+2,i+4,i+5])
        FB.extend([i+2,i+4])
        FR.extend([i+3,i+5])
    FR.append(3+mx*4);FB.append(2+mx*4)
    FB.reverse()
    fc.extend([FB,FR])
    #Yatay
    Y=(mx*4+4);V=mx*4+2
    for z in range(0,(my-1)*Y*2,Y*2):
        fc.extend([[z+Y+1,z+Y,z+Y+4+mx*4,z+Y+5+mx*4],[z+Y+V,z+Y+V+1,z+Y+V+5+mx*4,z+Y+V+4+mx*4]])
        for i in range(0,mx*4+2,2):fc.extend([[z+i+Y+0,z+i+Y+2,z+i+Y+V+4,z+i+Y+V+2],[z+i+Y  +3,z+i+Y  +1,z+i+Y+V+3,z+i+Y+V+5]])
        for i in range(0,mx*4-3,4):fc.extend([[z+i+Y+2,z+i+Y+3,z+i+Y  +5,z+i+Y  +4],[z+i+Y+V+5,z+i+Y+V+4,z+i+Y+V+6,z+i+Y+V+7]])
    #Dikey
    for Y in range(0,my):
        z=Y*(mx*4+4)*2
        for i in range(0,mx*4+2,4):fc.extend([[z+i+1,z+i+0,z+i+V+2,z+i+V+3],[z+i+3,z+i+1,z+i+V+3,z+i+V+5],[z+i+2,z+i+3,z+i+V+5,z+i+V+4],[z+i+0,z+i+2,z+i+V+4,z+i+V+2]])
    #Fitil-------------------
    if self.UST=='1':y1=my
    else:            y1=my-1
    for y in range(0,y1):
        for x in range(0,mx):
            if  kx[x][y]==True:
                Kapak(vr,fc,X,Z,x*2+1,y*2+1,k2/2,(k1+k2)*0.5-0.01)
                Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,(k1+k2)*0.5-0.01,k2)
            else:
                Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,0,0)
            m=len(fc);cam.extend([m-1,m-2])
            ftl.extend([m-3,m-4,m-5,m-6,m-7,m-8,m-9,m-10,m-11,m-12,m-13,m-14])
    #-----------------------------------------------------
    if  self.UST=='1':#Duz
        fc.append([UST[1],UST[0],SON[0],SON[1]])
        for i in range(0,mx*4,4):
            fc.append([ALT[i],ALT[i+1],ALT[i+3],ALT[i+2]])
        ON=[UST[0]]
        AR=[UST[1]]
        for i in range(0,len(ALT)-1,2):
            ON.append(ALT[i  ])
            AR.append(ALT[i+1])
        ON.append(SON[0])
        fc.append(ON)
        AR.append(SON[1])
        AR.reverse();fc.append(AR)
    elif self.UST=='2':#Yay
        if   self.DT2=='1':
            H=self.VL1/100
            if   H<0.01:H=  0.01;self.VL1=1
            elif H >= u:H=u-0.01;self.VL1=H*100
            h=sqrt(u**2+H**2)/2
            e=h*(u/H)
            C=sqrt(h**2+e**2)
            T1=Z[-1]-H
        elif self.DT2=='2':
            C=self.VL2/100
            if  C<u+0.01:
                C=u+0.01
                self.VL2=C*100
            T1=sqrt(C**2-u**2)+Z[-1]-C
        R=C-k1;F=R-k3*2
        K=R-k2;E=K-k3*2
        z=Z[-1]-C

        vr[UST[0]][2]=T1;vr[UST[1]][2]=T1
        vr[SON[0]][2]=T1;vr[SON[1]][2]=T1
        for i in ALT:vr[i][2]=sqrt(R**2-vr[i][0]**2)+z

        ON=[SON[0]];U1=[]
        for i in range(0,RES):
            A=i*pi/RES;x=cos(A)*C
            if  x>-u and x<u:
                vr.append([x,-k1/2,sin(A)*C+z]);ON.append(len(vr)-1)
        U1.extend(ON);U1.append(UST[0])
        ON.extend([UST[0],ALT[0]])
        AR=[];D1=[];D2=[]
        for i in range(0,len(ALT)-2,4):
            x1=vr[ALT[i+0]][0]; x2=vr[ALT[i+2]][0]
            ON.append(ALT[i+0]);AR.append(ALT[i+1])
            T1=[ALT[i+0]];      T2=[ALT[i+1]]
            for j in range(0,RES):
                A=j*pi/RES;x=-cos(A)*R
                if  x1<x and x<x2:
                    vr.extend([[x,-k1/2,sin(A)*R+z],[x,k1/2,sin(A)*R+z]])
                    ON.append(len(vr)-2);AR.append(len(vr)-1)
                    T1.append(len(vr)-2);T2.append(len(vr)-1)
            ON.append(ALT[i+2]);AR.append(ALT[i+3])
            T1.append(ALT[i+2]);T2.append(ALT[i+3])
            D1.append(T1);      D2.append(T2)
        AR.append(SON[1])
        U2=[SON[1]]
        for i in range(0,RES):
            A=i*pi/RES;x=cos(A)*C
            if  x>-u and x<u:
                vr.append([x,k1/2,sin(A)*C+z])
                AR.append(len(vr)-1);U2.append(len(vr)-1)
        AR.append(UST[1])
        U2.append(UST[1])
        AR.reverse()
        fc.extend([ON,AR])
        for i in range(0,len(U1)-1):fc.append([U1[i+1],U1[i],U2[i],U2[i+1]]);SM.append(len(fc)-1)
        for A in range(0,mx):
            for i in range(0,len(D1[A])-1):
                fc.append([D1[A][i+1],D1[A][i],D2[A][i],D2[A][i+1]]);SM.append(len(fc)-1)
        y=my-1
        for x in range(0,mx):
            if  kx[x][y]==True:
                fr=(k1+k2)*0.5-0.01;ek=k2
                R=C-k1;K=R-k2

                x1=X[x*2+1];x2=X[x*2+2]
                vr.extend([[x2,fr-k2/2,z+1  ],[x2-k2,fr-k2/2,z+1     ],[x2-k2,fr+k2/2,z+1     ],[x2,fr+k2/2,z+1  ]])
                vr.extend([[x2,fr-k2/2,Z[-3]],[x2-k2,fr-k2/2,Z[-3]+k2],[x2-k2,fr+k2/2,Z[-3]+k2],[x2,fr+k2/2,Z[-3]]])
                vr.extend([[x1,fr-k2/2,Z[-3]],[x1+k2,fr-k2/2,Z[-3]+k2],[x1+k2,fr+k2/2,Z[-3]+k2],[x1,fr+k2/2,Z[-3]]])
                vr.extend([[x1,fr-k2/2,z+1  ],[x1+k2,fr-k2/2,z+1     ],[x1+k2,fr+k2/2,z+1     ],[x1,fr+k2/2,z+1  ]])

                n=len(vr)
                fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10],[n-13,n-16,n-12,n- 9]])
                fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6],[n- 9,n-12,n- 8,n- 5]])
                fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2],[n- 5,n- 8,n- 4,n- 1]])
                ALT=[n-16,n-15,n-14,n-13,n-4,n-3,n-2,n-1]
                vr[ALT[0]][2]=sqrt(R**2-vr[ALT[0]][0]**2)+z;vr[ALT[1]][2]=sqrt(K**2-vr[ALT[1]][0]**2)+z
                vr[ALT[2]][2]=sqrt(K**2-vr[ALT[2]][0]**2)+z;vr[ALT[3]][2]=sqrt(R**2-vr[ALT[3]][0]**2)+z
                vr[ALT[4]][2]=sqrt(R**2-vr[ALT[4]][0]**2)+z;vr[ALT[5]][2]=sqrt(K**2-vr[ALT[5]][0]**2)+z
                vr[ALT[6]][2]=sqrt(K**2-vr[ALT[6]][0]**2)+z;vr[ALT[7]][2]=sqrt(R**2-vr[ALT[7]][0]**2)+z

                D1=[];D2=[];T1=[];T2=[]
                for i in range(0,RES):
                    A =i*pi/RES;y1=cos(A)*R;y2=-cos(A)*K
                    if x1   <y1 and y1<x2:   vr.extend([[y1,fr-k2/2,sin(A)*R+z],[y1,fr+k2/2,sin(A)*R+z]]);T1.append(len(vr)-2);T2.append(len(vr)-1)
                    if x1+k2<y2 and y2<x2-k2:vr.extend([[y2,fr-k2/2,sin(A)*K+z],[y2,fr+k2/2,sin(A)*K+z]]);D1.append(len(vr)-2);D2.append(len(vr)-1)
                ON=[ALT[1],ALT[0]];ON.extend(T1);ON.extend([ALT[4],ALT[5]]);ON.extend(D1)
                AR=[ALT[2],ALT[3]];AR.extend(T2);AR.extend([ALT[7],ALT[6]]);AR.extend(D2);AR.reverse()

                if   D1==[] and T1==[]:fc.extend([ON,AR,[ALT[5],ALT[6],ALT[2],ALT[1]],[ALT[7],ALT[4],ALT[0],ALT[3]]]);                                                        m=len(fc);SM.extend([m-1,m-2])
                elif D1==[] and T1!=[]:fc.extend([ON,AR,[ALT[5],ALT[6],ALT[2],ALT[1]],[ALT[7],ALT[4],T1[-1],T2[-1]],[ALT[0],ALT[3],T2[0],T1[0]]]);                            m=len(fc);SM.extend([m-1,m-2,m-3])
                elif D1!=[] and T1==[]:fc.extend([ON,AR,[ALT[5],ALT[6],D2[0],D1[0]],[ALT[2],ALT[1],D1[-1],D2[-1]],[ALT[7],ALT[4],ALT[0],ALT[3]]]);                            m=len(fc);SM.extend([m-1,m-2,m-3])
                else:                  fc.extend([ON,AR,[ALT[5],ALT[6],D2[0],D1[0]],[ALT[2],ALT[1],D1[-1],D2[-1]],[ALT[7],ALT[4],T1[-1],T2[-1]],[ALT[0],ALT[3],T2[0],T1[0]]]);m=len(fc);SM.extend([m-1,m-2,m-3,m-4])

                for i in range(0,len(D1)-1):fc.append([D1[i+1],D1[i],D2[i],D2[i+1]]);SM.append(len(fc)-1)
                for i in range(0,len(T1)-1):fc.append([T1[i+1],T1[i],T2[i],T2[i+1]]);SM.append(len(fc)-1)
                R=C-k1-k2;K=R-k3*2
            else:
                fr=0;ek=0
                R=C-k1;K=R-k3*2
            #Fitil
            x1=X[x*2+1]+ek;x2=X[x*2+2]-ek
            vr.extend([[x2,fr-k3,z+1     ],[x2-k3*2,fr-k3,z+1          ],[x2-k3*2,fr+k3,z+1          ],[x2,fr+k3,z+1     ]])
            vr.extend([[x2,fr-k3,Z[-3]+ek],[x2-k3*2,fr-k3,Z[-3]+ek+k3*2],[x2-k3*2,fr+k3,Z[-3]+ek+k3*2],[x2,fr+k3,Z[-3]+ek]])
            vr.extend([[x1,fr-k3,Z[-3]+ek],[x1+k3*2,fr-k3,Z[-3]+ek+k3*2],[x1+k3*2,fr+k3,Z[-3]+ek+k3*2],[x1,fr+k3,Z[-3]+ek]])
            vr.extend([[x1,fr-k3,z+1     ],[x1+k3*2,fr-k3,z+1          ],[x1+k3*2,fr+k3,z+1          ],[x1,fr+k3,z+1     ]])
            n=len(vr)
            fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10]])
            fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6]])
            fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2]])
            m=len(fc);ftl.extend([m-1,m-2,m-3,m-4,m-5,m-6,m-7,m-8,m-9])
            ALT=[n-16,n-15,n-14,n-13,n-4,n-3,n-2,n-1]
            vr[ALT[0]][2]=sqrt(R**2-vr[ALT[0]][0]**2)+z;vr[ALT[1]][2]=sqrt(K**2-vr[ALT[1]][0]**2)+z
            vr[ALT[2]][2]=sqrt(K**2-vr[ALT[2]][0]**2)+z;vr[ALT[3]][2]=sqrt(R**2-vr[ALT[3]][0]**2)+z
            vr[ALT[4]][2]=sqrt(R**2-vr[ALT[4]][0]**2)+z;vr[ALT[5]][2]=sqrt(K**2-vr[ALT[5]][0]**2)+z
            vr[ALT[6]][2]=sqrt(K**2-vr[ALT[6]][0]**2)+z;vr[ALT[7]][2]=sqrt(R**2-vr[ALT[7]][0]**2)+z
            D1=[];D2=[];T1=[];T2=[]
            for i in range(0,RES):
                A =i*pi/RES;y1=cos(A)*R;y2=-cos(A)*K
                if x1     <y1 and y1<x2:     vr.extend([[y1,fr-k3,sin(A)*R+z],[y1,fr+k3,sin(A)*R+z]]);T1.append(len(vr)-2);T2.append(len(vr)-1);ftl.extend([len(fc)-1,len(fc)-2])
                if x1+k3*2<y2 and y2<x2-k3*2:vr.extend([[y2,fr-k3,sin(A)*K+z],[y2,fr+k3,sin(A)*K+z]]);D1.append(len(vr)-2);D2.append(len(vr)-1);ftl.extend([len(fc)-1,len(fc)-2])
            ON=[ALT[1],ALT[0]];ON.extend(T1);ON.extend([ALT[4],ALT[5]]);ON.extend(D1)
            AR=[ALT[2],ALT[3]];AR.extend(T2);AR.extend([ALT[7],ALT[6]]);AR.extend(D2);AR.reverse()

            if  D1==[]:fc.extend([ON,AR,[ALT[5],ALT[6],ALT[2],ALT[1]]]);                            m=len(fc);ftl.extend([m-1,m-2,m-3    ]);SM.extend([m-1    ])
            else:      fc.extend([ON,AR,[ALT[5],ALT[6],D2[0],D1[0]],[ALT[2],ALT[1],D1[-1],D2[-1]]]);m=len(fc);ftl.extend([m-1,m-2,m-3,m-4]);SM.extend([m-1,m-2])

            for i in range(0,len(D1)-1):fc.append([D1[i+1],D1[i],D2[i],D2[i+1]]);ftl.append(len(fc)-1);SM.append(len(fc)-1)
            #Cam
            x1=X[x*2+1]+ek+k3*2;x2=X[x*2+2]-ek-k3*2
            ON=[];AR=[]
            for i in range(0,RES):
                A= i*pi/RES;y1=-cos(A)*K
                if  x1<y1 and y1<x2:
                    vr.extend([[y1,fr-0.005,sin(A)*K+z],[y1,fr+0.005,sin(A)*K+z]])
                    n=len(vr);ON.append(n-1);AR.append(n-2)
            vr.extend([[x1,fr-0.005,sqrt(K**2-x1**2)+z],[x1,fr+0.005,sqrt(K**2-x1**2)+z]])
            vr.extend([[x1,fr-0.005,Z[-3]+ek+k3*2     ],[x1,fr+0.005,Z[-3]+ek+k3*2     ]])
            vr.extend([[x2,fr-0.005,Z[-3]+ek+k3*2     ],[x2,fr+0.005,Z[-3]+ek+k3*2     ]])
            vr.extend([[x2,fr-0.005,sqrt(K**2-x2**2)+z],[x2,fr+0.005,sqrt(K**2-x2**2)+z]])
            n=len(vr);ON.extend([n-1,n-3,n-5,n-7]);AR.extend([n-2,n-4,n-6,n-8])
            fc.append(ON);AR.reverse();fc.append(AR)
            m=len(fc);cam.extend([m-1,m-2])

    elif self.UST=='3':#Egri
        if   self.DT3=='1':H=(self.VL1/200)/u
        elif self.DT3=='2':H=self.VL3/100
        elif self.DT3=='3':H=sin(self.VL4*pi/180)/cos(self.VL4*pi/180)
        z=sqrt(k1**2+(k1*H)**2)
        k=sqrt(k2**2+(k2*H)**2)
        f=sqrt(k3**2+(k3*H)**2)*2
        vr[UST[0]][2]=Z[-1]+vr[UST[0]][0]*H
        vr[UST[1]][2]=Z[-1]+vr[UST[1]][0]*H
        for i in ALT:
            vr[i][2] =Z[-1]+vr[i][0]*H-z
        vr[SON[0]][2]=Z[-1]+vr[SON[0]][0]*H
        vr[SON[1]][2]=Z[-1]+vr[SON[1]][0]*H
        fc.append([UST[1],UST[0], SON[0],SON[1] ])
        for i in range(0,mx*4,4):
            fc.append([ALT[i],ALT[i+1],ALT[i+3],ALT[i+2]])
        ON=[UST[0]]
        AR=[UST[1]]
        for i in range(0,len(ALT)-1,2):
            ON.append(ALT[i  ])
            AR.append(ALT[i+1])
        ON.append(SON[0])
        fc.append(ON)
        AR.append(SON[1])
        AR.reverse();fc.append(AR)
        y=my-1
        for x in range(0,mx):
            if  kx[x][y]==True:
                Kapak(vr,fc,X,Z,x*2+1,y*2+1,k2/2,(k1+k2)*0.5-0.01)
                n=len(vr)
                vr[n- 5][2]=Z[-1]+vr[n- 5][0]*H-z
                vr[n- 6][2]=Z[-1]+vr[n- 6][0]*H-z-k
                vr[n- 7][2]=Z[-1]+vr[n- 7][0]*H-z-k
                vr[n- 8][2]=Z[-1]+vr[n- 8][0]*H-z
                vr[n- 9][2]=Z[-1]+vr[n- 9][0]*H-z
                vr[n-10][2]=Z[-1]+vr[n-10][0]*H-z-k
                vr[n-11][2]=Z[-1]+vr[n-11][0]*H-z-k
                vr[n-12][2]=Z[-1]+vr[n-12][0]*H-z
                Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,(k1+k2)*0.5-0.01,k2)
                n=len(vr)
                vr[n- 2][2]=Z[-1]+vr[n- 2][0]*H-z-k-f
                vr[n- 3][2]=Z[-1]+vr[n- 3][0]*H-z-k-f
                vr[n- 6][2]=Z[-1]+vr[n- 6][0]*H-z-k-f
                vr[n- 7][2]=Z[-1]+vr[n- 7][0]*H-z-k-f
                vr[n-13][2]=Z[-1]+vr[n-13][0]*H-z-k
                vr[n-14][2]=Z[-1]+vr[n-14][0]*H-z-k-f
                vr[n-15][2]=Z[-1]+vr[n-15][0]*H-z-k-f
                vr[n-16][2]=Z[-1]+vr[n-16][0]*H-z-k
                vr[n-17][2]=Z[-1]+vr[n-17][0]*H-z-k
                vr[n-18][2]=Z[-1]+vr[n-18][0]*H-z-k-f
                vr[n-19][2]=Z[-1]+vr[n-19][0]*H-z-k-f
                vr[n-20][2]=Z[-1]+vr[n-20][0]*H-z-k
            else:
                Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,0,0)
                n=len(vr)
                vr[n-2][2]=Z[-1]+vr[n-2][0]*H-z-f
                vr[n-3][2]=Z[-1]+vr[n-3][0]*H-z-f
                vr[n-6][2]=Z[-1]+vr[n-6][0]*H-z-f
                vr[n-7][2]=Z[-1]+vr[n-7][0]*H-z-f
                vr[n-13][2]=Z[-1]+vr[n-13][0]*H-z
                vr[n-14][2]=Z[-1]+vr[n-14][0]*H-z-f
                vr[n-15][2]=Z[-1]+vr[n-15][0]*H-z-f
                vr[n-16][2]=Z[-1]+vr[n-16][0]*H-z
                vr[n-17][2]=Z[-1]+vr[n-17][0]*H-z
                vr[n-18][2]=Z[-1]+vr[n-18][0]*H-z-f
                vr[n-19][2]=Z[-1]+vr[n-19][0]*H-z-f
                vr[n-20][2]=Z[-1]+vr[n-20][0]*H-z
            m=len(fc);cam.extend([m-1,m-2])
            ftl.extend([m-3,m-4,m-5,m-6,m-7,m-8,m-9,m-10,m-11,m-12,m-13,m-14])
    elif self.UST=='4':#Ucgen
        if   self.DT3=='1':H=(self.VL1/100)/u
        elif self.DT3=='2':H=self.VL3/100
        elif self.DT3=='3':H=sin(self.VL4*pi/180)/cos(self.VL4*pi/180)
        z=sqrt(k1**2+(k1*H)**2)
        k=sqrt(k2**2+(k2*H)**2)
        f=sqrt(k3**2+(k3*H)**2)*2
        vr[UST[0]][2]=Z[-1]+vr[UST[0]][0]*H
        vr[UST[1]][2]=Z[-1]+vr[UST[1]][0]*H
        for i in ALT:
            vr[i][2] =Z[-1]-abs(vr[i][0])*H-z
        vr[SON[0]][2]=Z[-1]-vr[SON[0]][0]*H
        vr[SON[1]][2]=Z[-1]-vr[SON[1]][0]*H
        vr.extend([[0,-k1/2,Z[-1]],[0, k1/2,Z[-1]]])

        x = 0
        for j in range(2,len(ALT)-2,4):
            if vr[ALT[j]][0]<0 and 0<vr[ALT[j+2]][0]:x=1

        n=len(vr)
        fc.extend([[UST[1],UST[0],n-2,n-1],[n-1,n-2,SON[0],SON[1]]])
        ON=[SON[0],n-2,UST[0]];AR=[SON[1],n-1,UST[1]]

        if  x==0:vr.extend([[0,-k1/2,Z[-1]-z],[0,k1/2,Z[-1]-z]])
        for j in range(0,len(ALT)-2,4):
            if  vr[ALT[j]][0]<0 and vr[ALT[j+2]][0]<0:
                fc.append([ALT[j],ALT[j+1],ALT[j+3],ALT[j+2]])
                ON.extend([ALT[j  ],ALT[j+2]])
                AR.extend([ALT[j+1],ALT[j+3]])
            elif vr[ALT[j]][0]>0 and vr[ALT[j+2]][0]>0:
                fc.append([ALT[j],ALT[j+1],ALT[j+3],ALT[j+2]])
                ON.extend([ALT[j  ],ALT[j+2]])
                AR.extend([ALT[j+1],ALT[j+3]])
            else:
                n=len(vr)
                fc.extend([[ALT[j],ALT[j+1],n-1,n-2],[n-2,n-1,ALT[j+3],ALT[j+2]]])
                ON.extend([ALT[j+0],n-2,ALT[j+2]])
                AR.extend([ALT[j+1],n-1,ALT[j+3]])
        fc.append(ON);AR.reverse();fc.append(AR)
        y=my-1
        for x in range(0,mx):
            if  vr[ALT[x*4]][0]<0 and vr[ALT[x*4+2]][0]<0:
                if  kx[x][y]==True:
                    Kapak(vr,fc,X,Z,x*2+1,y*2+1,k2/2,(k1+k2)*0.5-0.01)
                    n=len(vr)
                    vr[n- 5][2]=Z[-1]+vr[n- 5][0]*H-z
                    vr[n- 6][2]=Z[-1]+vr[n- 6][0]*H-z-k
                    vr[n- 7][2]=Z[-1]+vr[n- 7][0]*H-z-k
                    vr[n- 8][2]=Z[-1]+vr[n- 8][0]*H-z
                    vr[n- 9][2]=Z[-1]+vr[n- 9][0]*H-z
                    vr[n-10][2]=Z[-1]+vr[n-10][0]*H-z-k
                    vr[n-11][2]=Z[-1]+vr[n-11][0]*H-z-k
                    vr[n-12][2]=Z[-1]+vr[n-12][0]*H-z
                    Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,(k1+k2)*0.5-0.01,k2)
                    n=len(vr)
                    vr[n- 2][2]=Z[-1]+vr[n- 2][0]*H-z-k-f
                    vr[n- 3][2]=Z[-1]+vr[n- 3][0]*H-z-k-f
                    vr[n- 6][2]=Z[-1]+vr[n- 6][0]*H-z-k-f
                    vr[n- 7][2]=Z[-1]+vr[n- 7][0]*H-z-k-f
                    vr[n-13][2]=Z[-1]+vr[n-13][0]*H-z-k
                    vr[n-14][2]=Z[-1]+vr[n-14][0]*H-z-k-f
                    vr[n-15][2]=Z[-1]+vr[n-15][0]*H-z-k-f
                    vr[n-16][2]=Z[-1]+vr[n-16][0]*H-z-k
                    vr[n-17][2]=Z[-1]+vr[n-17][0]*H-z-k
                    vr[n-18][2]=Z[-1]+vr[n-18][0]*H-z-k-f
                    vr[n-19][2]=Z[-1]+vr[n-19][0]*H-z-k-f
                    vr[n-20][2]=Z[-1]+vr[n-20][0]*H-z-k
                else:
                    Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,0,0)
                    n=len(vr)
                    vr[n-2][2]=Z[-1]+vr[n-2][0]*H-z-f
                    vr[n-3][2]=Z[-1]+vr[n-3][0]*H-z-f
                    vr[n-6][2]=Z[-1]+vr[n-6][0]*H-z-f
                    vr[n-7][2]=Z[-1]+vr[n-7][0]*H-z-f
                    vr[n-13][2]=Z[-1]+vr[n-13][0]*H-z
                    vr[n-14][2]=Z[-1]+vr[n-14][0]*H-z-f
                    vr[n-15][2]=Z[-1]+vr[n-15][0]*H-z-f
                    vr[n-16][2]=Z[-1]+vr[n-16][0]*H-z
                    vr[n-17][2]=Z[-1]+vr[n-17][0]*H-z
                    vr[n-18][2]=Z[-1]+vr[n-18][0]*H-z-f
                    vr[n-19][2]=Z[-1]+vr[n-19][0]*H-z-f
                    vr[n-20][2]=Z[-1]+vr[n-20][0]*H-z
                m=len(fc);cam.extend([m-1,m-2])
                ftl.extend([m-3,m-4,m-5,m-6,m-7,m-8,m-9,m-10,m-11,m-12,m-13,m-14])
            elif vr[ALT[x*4]][0]>0 and vr[ALT[x*4+2]][0]>0:
                if  kx[x][y]==True:
                    Kapak(vr,fc,X,Z,x*2+1,y*2+1,k2/2,(k1+k2)*0.5-0.01)
                    n=len(vr)
                    vr[n- 5][2]=Z[-1]-vr[n- 5][0]*H-z
                    vr[n- 6][2]=Z[-1]-vr[n- 6][0]*H-z-k
                    vr[n- 7][2]=Z[-1]-vr[n- 7][0]*H-z-k
                    vr[n- 8][2]=Z[-1]-vr[n- 8][0]*H-z
                    vr[n- 9][2]=Z[-1]-vr[n- 9][0]*H-z
                    vr[n-10][2]=Z[-1]-vr[n-10][0]*H-z-k
                    vr[n-11][2]=Z[-1]-vr[n-11][0]*H-z-k
                    vr[n-12][2]=Z[-1]-vr[n-12][0]*H-z
                    Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,(k1+k2)*0.5-0.01,k2)
                    n=len(vr)
                    vr[n- 2][2]=Z[-1]-vr[n- 2][0]*H-z-k-f
                    vr[n- 3][2]=Z[-1]-vr[n- 3][0]*H-z-k-f
                    vr[n- 6][2]=Z[-1]-vr[n- 6][0]*H-z-k-f
                    vr[n- 7][2]=Z[-1]-vr[n- 7][0]*H-z-k-f
                    vr[n-13][2]=Z[-1]-vr[n-13][0]*H-z-k
                    vr[n-14][2]=Z[-1]-vr[n-14][0]*H-z-k-f
                    vr[n-15][2]=Z[-1]-vr[n-15][0]*H-z-k-f
                    vr[n-16][2]=Z[-1]-vr[n-16][0]*H-z-k
                    vr[n-17][2]=Z[-1]-vr[n-17][0]*H-z-k
                    vr[n-18][2]=Z[-1]-vr[n-18][0]*H-z-k-f
                    vr[n-19][2]=Z[-1]-vr[n-19][0]*H-z-k-f
                    vr[n-20][2]=Z[-1]-vr[n-20][0]*H-z-k
                else:
                    Fitil(vr,fc,X,Z,x*2+1,y*2+1,k3,0,0)
                    n=len(vr)
                    vr[n-2][2]=Z[-1]-vr[n-2][0]*H-z-f
                    vr[n-3][2]=Z[-1]-vr[n-3][0]*H-z-f
                    vr[n-6][2]=Z[-1]-vr[n-6][0]*H-z-f
                    vr[n-7][2]=Z[-1]-vr[n-7][0]*H-z-f
                    vr[n-13][2]=Z[-1]-vr[n-13][0]*H-z
                    vr[n-14][2]=Z[-1]-vr[n-14][0]*H-z-f
                    vr[n-15][2]=Z[-1]-vr[n-15][0]*H-z-f
                    vr[n-16][2]=Z[-1]-vr[n-16][0]*H-z
                    vr[n-17][2]=Z[-1]-vr[n-17][0]*H-z
                    vr[n-18][2]=Z[-1]-vr[n-18][0]*H-z-f
                    vr[n-19][2]=Z[-1]-vr[n-19][0]*H-z-f
                    vr[n-20][2]=Z[-1]-vr[n-20][0]*H-z
                m=len(fc);cam.extend([m-1,m-2])
                ftl.extend([m-3,m-4,m-5,m-6,m-7,m-8,m-9,m-10,m-11,m-12,m-13,m-14])
            else:
                k4=k3*2
                if  kx[x][y]==True:
                    zz=(k1+k2)*0.5-0.01
                    xx=X[x*2+1]
                    vr.extend([[xx,-k2/2+zz,Z[-3]       ],[xx+k2,-k2/2+zz,Z[-3]    +k2       ],[xx+k2,k2/2+zz,Z[-3]    +k2       ],[xx,k2/2+zz,Z[-3]       ]])
                    vr.extend([[xx,-k2/2+zz,Z[-1]+xx*H-z],[xx+k2,-k2/2+zz,Z[-1]+(xx+k2)*H-z-k],[xx+k2,k2/2+zz,Z[-1]+(xx+k2)*H-z-k],[xx,k2/2+zz,Z[-1]+xx*H-z]])
                    vr.extend([[ 0,-k2/2+zz,Z[-1]     -z],[    0,-k2/2+zz,Z[-1]          -z-k],[    0,k2/2+zz,Z[-1]          -z-k],[ 0,k2/2+zz,Z[-1]     -z]])
                    xx=X[x*2+2]
                    vr.extend([[xx,-k2/2+zz,Z[-1]-xx*H-z],[xx-k2,-k2/2+zz,Z[-1]-(xx-k2)*H-z-k],[xx-k2,k2/2+zz,Z[-1]-(xx-k2)*H-z-k],[xx,k2/2+zz,Z[-1]-xx*H-z]])
                    vr.extend([[xx,-k2/2+zz,Z[-3]       ],[xx-k2,-k2/2+zz,Z[-3]    +k2       ],[xx-k2,k2/2+zz,Z[-3]    +k2       ],[xx,k2/2+zz,Z[-3]       ]])
                    n=len(vr)
                    fc.extend([[n-20,n-19,n-15,n-16],[n-19,n-18,n-14,n-15],[n-18,n-17,n-13,n-14],[n-17,n-20,n-16,n-13]])
                    fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10],[n-13,n-16,n-12,n- 9]])
                    fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6],[n- 9,n-12,n- 8,n- 5]])
                    fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2],[n- 5,n- 8,n- 4,n- 1]])
                    fc.extend([[n- 4,n- 3,n-19,n-20],[n- 3,n- 2,n-18,n-19],[n- 2,n- 1,n-17,n-18],[n- 1,n- 4,n-20,n-17]])
                    xx=X[x*2+1]
                    vr.extend([[xx   +k2,-k3+zz,Z[-3]    +k2            ],[xx+k4+k2,-k3+zz,Z[-3]    +k2+k4         ],[xx+k4+k2, k3+zz,Z[-3]    +k2+k4         ],[xx   +k2, k3+zz,Z[-3]    +k2            ]])
                    vr.extend([[xx   +k2,-k3+zz,Z[-1]+(xx+k2   )*H-z-k  ],[xx+k4+k2,-k3+zz,Z[-1]+(xx+k2+k4)*H-z-k-f],[xx+k4+k2, k3+zz,Z[-1]+(xx+k2+k4)*H-z-k-f],[xx   +k2, k3+zz,Z[-1]+(xx+k2   )*H-z-k  ]])
                    vr.extend([[    0,-k3+zz,Z[-1]-k     -z],[       0,-k3+zz,Z[-1]-k             -z-f],[       0,k3+zz,Z[-1]-k          -z-f],[    0,k3+zz,Z[-1]-k     -z]])
                    xx=X[x*2+2]
                    vr.extend([[xx   -k2,-k3+zz,Z[-1]-(xx-k2   )*H-z-k  ],[xx-k4-k2,-k3+zz,Z[-1]-(xx-k2-k4)*H-z-k-f],[xx-k4-k2, k3+zz,Z[-1]-(xx-k2-k4)*H-z-k-f],[xx   -k2, k3+zz,Z[-1]-(xx-k2   )*H-z-k  ]])
                    vr.extend([[xx   -k2,-k3+zz,Z[-3]    +k2            ],[xx-k4-k2,-k3+zz,Z[-3]    +k2+k4         ],[xx-k4-k2, k3+zz,Z[-3]    +k2+k4         ],[xx   -k2, k3+zz,Z[-3]    +k2            ]])
                    n=len(vr)
                    fc.extend([[n-20,n-19,n-15,n-16],[n-19,n-18,n-14,n-15],[n-18,n-17,n-13,n-14]])
                    fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10]])
                    fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6]])
                    fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2]])
                    fc.extend([[n- 4,n- 3,n-19,n-20],[n- 3,n- 2,n-18,n-19],[n- 2,n- 1,n-17,n-18]])
                    xx=X[x*2+1]
                    vr.extend([[xx+k4+k2,-k3+zz,Z[-3]    +k2+k4         ],[xx+k4+k2, k3+zz,Z[-3]    +k2+k4         ]])
                    vr.extend([[xx+k4+k2,-k3+zz,Z[-1]+(xx+k2+k4)*H-z-k-f],[xx+k4+k2, k3+zz,Z[-1]+(xx+k2+k4)*H-z-k-f]])
                    vr.extend([[       0,-k3+zz,Z[-1]-k             -z-f],[       0,k3+zz,Z[-1]-k          -z-f]])
                    xx=X[x*2+2]
                    vr.extend([[xx-k4-k2,-k3+zz,Z[-1]-(xx-k2-k4)*H-z-k-f],[xx-k4-k2, k3+zz,Z[-1]-(xx-k2-k4)*H-z-k-f]])
                    vr.extend([[xx-k4-k2,-k3+zz,Z[-3]    +k2+k4         ],[xx-k4-k2, k3+zz,Z[-3]    +k2+k4         ]])
                    fc.extend([[n+8,n+6,n+4,n+2,n+0],[n+1,n+3,n+5,n+7,n+9]])
                else:
                    xx=X[x*2+1]
                    vr.extend([[xx,-k3,Z[-3]       ],[xx+k4,-k3,Z[-3]    +k4       ],[xx+k4,k3,Z[-3]    +k4       ],[xx,k3,Z[-3]       ]])
                    vr.extend([[xx,-k3,Z[-1]+xx*H-z],[xx+k4,-k3,Z[-1]+(xx+k4)*H-z-f],[xx+k4,k3,Z[-1]+(xx+k4)*H-z-f],[xx,k3,Z[-1]+xx*H-z]])
                    vr.extend([[ 0,-k3,Z[-1]     -z],[    0,-k3,Z[-1]          -z-f],[    0,k3,Z[-1]          -z-f],[ 0,k3,Z[-1]     -z]])
                    xx=X[x*2+2]
                    vr.extend([[xx,-k3,Z[-1]-xx*H-z],[xx-k4,-k3,Z[-1]-(xx-k4)*H-z-f],[xx-k4,k3,Z[-1]-(xx-k4)*H-z-f],[xx,k3,Z[-1]-xx*H-z]])
                    vr.extend([[xx,-k3,Z[-3]       ],[xx-k4,-k3,Z[-3]    +k4       ],[xx-k4,k3,Z[-3]    +k4       ],[xx,k3,Z[-3]       ]])
                    n=len(vr)
                    fc.extend([[n-20,n-19,n-15,n-16],[n-19,n-18,n-14,n-15],[n-18,n-17,n-13,n-14]])
                    fc.extend([[n-16,n-15,n-11,n-12],[n-15,n-14,n-10,n-11],[n-14,n-13,n- 9,n-10]])
                    fc.extend([[n-12,n-11,n- 7,n- 8],[n-11,n-10,n- 6,n- 7],[n-10,n- 9,n- 5,n- 6]])
                    fc.extend([[n- 8,n- 7,n- 3,n- 4],[n- 7,n- 6,n- 2,n- 3],[n- 6,n- 5,n- 1,n- 2]])
                    fc.extend([[n- 4,n- 3,n-19,n-20],[n- 3,n- 2,n-18,n-19],[n- 2,n- 1,n-17,n-18]])
                    xx=X[x*2+1]
                    vr.extend([[xx+k4,-0.005,Z[-3]    +k4       ],[xx+k4,0.005,Z[-3]    +k4       ]])
                    vr.extend([[xx+k4,-0.005,Z[-1]+(xx+k4)*H-z-f],[xx+k4,0.005,Z[-1]+(xx+k4)*H-z-f]])
                    vr.extend([[    0,-0.005,Z[-1]          -z-f],[    0,0.005,Z[-1]          -z-f]])
                    xx=X[x*2+2]
                    vr.extend([[xx-k4,-0.005,Z[-1]-(xx-k4)*H-z-f],[xx-k4,0.005,Z[-1]-(xx-k4)*H-z-f]])
                    vr.extend([[xx-k4,-0.005,Z[-3]    +k4       ],[xx-k4,0.005,Z[-3]    +k4       ]])
                    fc.extend([[n+8,n+6,n+4,n+2,n+0],[n+1,n+3,n+5,n+7,n+9]])
                m=len(fc);cam.extend([m-1,m-2])
                ftl.extend([m-3,m-4,m-5,m-6,m-7,m-8,m-9,m-10,m-11,m-12,m-13,m-14,m-15,m-16,m-17])
    #Mermer
    if  self.mr==True:
        mrh=-self.mr1/100;mrg= self.mr2/100
        mdv=(self.mr3/200)+mrg;msv=-(mdv+(self.mr4/100))
        vr.extend([[-u,mdv,0],[u,mdv,0],[-u,msv,0],[u,msv,0],[-u,mdv,mrh],[u,mdv,mrh],[-u,msv,mrh],[u,msv,mrh]])
        n=len(vr);fc.extend([[n-1,n-2,n-4,n-3],[n-3,n-4,n-8,n-7],[n-6,n-5,n-7,n-8],[n-2,n-1,n-5,n-6],[n-4,n-2,n-6,n-8],[n-5,n-1,n-3,n-7]])
        n=len(fc);mer.extend([n-1,n-2,n-3,n-4,n-5,n-6])
#OBJE -----------------------------------------------------------
    mesh = bpy.data.meshes.new(name='Window')
    mesh.from_pydata(vr,[],fc)
    if   self.mt1=='1':mesh.materials.append(MAT('PVC',    1.0,1.0,1.0))
    elif self.mt1=='2':mesh.materials.append(MAT('Wood',   0.3,0.2,0.1))
    elif self.mt1=='3':mesh.materials.append(MAT('Plastic',0.0,0.0,0.0))

    if   self.mt2=='1':mesh.materials.append(MAT('PVC',    1.0,1.0,1.0))
    elif self.mt2=='2':mesh.materials.append(MAT('Wood',   0.3,0.2,0.1))
    elif self.mt2=='3':mesh.materials.append(MAT('Plastic',0.0,0.0,0.0))

    mesh.materials.append(MAT('Glass',0.5,0.8,1.0))
    if self.mr==True:mesh.materials.append(MAT('Marble', 0.9,0.8,0.7))

    for i in ftl:
        mesh.polygons[i].material_index=1
    for i in cam:
        mesh.polygons[i].material_index=2
    for i in mer:
        mesh.polygons[i].material_index=3
    for i in SM:
        mesh.polygons[i].use_smooth = 1
    mesh.update(calc_edges=True)
    from bpy_extras import object_utils
    object_utils.object_data_add(context, mesh, operator=None)
    return mesh.name
    if  bpy.context.mode!='EDIT_MESH':
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
#----------------------------------------------------------------
class PENCERE(bpy.types.Operator):
    bl_idname = "mesh.add_say3d_pencere2"
    bl_label = "Window"
    bl_description = "Window Generator"
    bl_options = {'REGISTER', 'UNDO'}
    prs = EnumProperty(items = (('1',"WINDOW 250X200",""),
                                ('2',"WINDOW 200X200",""),
                                ('3',"WINDOW 180X200",""),
                                ('4',"WINDOW 180X160",""),
                                ('5',"WINDOW 160X160",""),
                                ('6',"WINDOW 50X50",""),
                                ('7',"DOOR 80X250",""),
                                ('8',"DOOR 80X230","")),
                                name="")
    son=prs
    gen=IntProperty(name='H Count',     min=1,max= 8, default= 3, description='Horizontal Panes')
    yuk=IntProperty(name='V Count',     min=1,max= 5, default= 1, description='Vertical Panes')
    kl1=IntProperty(name='Outer Frame', min=2,max=50, default= 5, description='Outside Frame Thickness')
    kl2=IntProperty(name='Risers',      min=2,max=50, default= 5, description='Risers Width')
    fk =IntProperty(name='Inner Frame', min=1,max=20, default= 2, description='Inside Frame Thickness')

    mr=BoolProperty(name='Sill', default=True,description='Window Sill')
    mr1=IntProperty(name='',min=1, max=20, default= 4, description='Height')
    mr2=IntProperty(name='',min=0, max=20, default= 4, description='First Depth')
    mr3=IntProperty(name='',min=1, max=50, default=20, description='Second Depth')
    mr4=IntProperty(name='',min=0, max=50, default= 0, description='Extrusion for Jamb')

    mt1=EnumProperty(items =(('1',"PVC",""),('2',"WOOD",""),('3',"Plastic","")),name="",default='1')
    mt2=EnumProperty(items =(('1',"PVC",""),('2',"WOOD",""),('3',"Plastic","")),name="",default='3')

    UST=EnumProperty(items =(('1',"Flat",""),('2',"Arch",  ""),('3',"Inclined", ""),('4',"Triangle","")),name="Top",default='1')
    DT2=EnumProperty(items =(('1',"Difference",""),('2',"Radius",   "")),                         name="",default='1')
    DT3=EnumProperty(items =(('1',"Difference",""),('2',"Incline %",""),('3',"Incline Angle","")),name="",default='1')

    VL1=IntProperty( name='',min=-10000,max=10000,default=30)#Fark
    VL2=IntProperty( name='',min=     1,max=10000,default=30)#Cap
    VL3=IntProperty( name='',min=  -100,max=  100,default=30)#Egim %
    VL4=IntProperty( name='',min=   -45,max=   45,default=30)#Egim Aci

    RES=IntProperty(name='Resolution pi/',min=2,max=360,default=36)#Res

    gnx0=IntProperty(name='',min=1,max=300,default= 60,description='1st Window Width')
    gnx1=IntProperty(name='',min=1,max=300,default=110,description='2nd Window Width')
    gnx2=IntProperty(name='',min=1,max=300,default= 60,description='3rd Window Width')
    gnx3=IntProperty(name='',min=1,max=300,default= 60,description='4th Window Width')
    gnx4=IntProperty(name='',min=1,max=300,default= 60,description='5th Window Width')
    gnx5=IntProperty(name='',min=1,max=300,default= 60,description='6th Window Width')
    gnx6=IntProperty(name='',min=1,max=300,default= 60,description='7th Window Width')
    gnx7=IntProperty(name='',min=1,max=300,default= 60,description='8th Window Width')

    gny0=IntProperty(name='',min=1,max=300,default=190,description='1st Row Height')
    gny1=IntProperty(name='',min=1,max=300,default= 45,description='2nd Row Height')
    gny2=IntProperty(name='',min=1,max=300,default= 45,description='3rd Row Height')
    gny3=IntProperty(name='',min=1,max=300,default= 45,description='4th Row Height')
    gny4=IntProperty(name='',min=1,max=300,default= 45,description='5th Row Height')

    k00=BoolProperty(name='',default=True); k01=BoolProperty(name='',default=False)
    k02=BoolProperty(name='',default=True); k03=BoolProperty(name='',default=False)
    k04=BoolProperty(name='',default=False);k05=BoolProperty(name='',default=False)
    k06=BoolProperty(name='',default=False);k07=BoolProperty(name='',default=False)

    k10=BoolProperty(name='',default=False);k11=BoolProperty(name='',default=False)
    k12=BoolProperty(name='',default=False);k13=BoolProperty(name='',default=False)
    k14=BoolProperty(name='',default=False);k15=BoolProperty(name='',default=False)
    k16=BoolProperty(name='',default=False);k17=BoolProperty(name='',default=False)

    k20=BoolProperty(name='',default=False);k21=BoolProperty(name='',default=False)
    k22=BoolProperty(name='',default=False);k23=BoolProperty(name='',default=False)
    k24=BoolProperty(name='',default=False);k25=BoolProperty(name='',default=False)
    k26=BoolProperty(name='',default=False);k27=BoolProperty(name='',default=False)

    k30=BoolProperty(name='',default=False);k31=BoolProperty(name='',default=False)
    k32=BoolProperty(name='',default=False);k33=BoolProperty(name='',default=False)
    k34=BoolProperty(name='',default=False);k35=BoolProperty(name='',default=False)
    k36=BoolProperty(name='',default=False);k37=BoolProperty(name='',default=False)

    k40=BoolProperty(name='',default=False);k41=BoolProperty(name='',default=False)
    k42=BoolProperty(name='',default=False);k43=BoolProperty(name='',default=False)
    k44=BoolProperty(name='',default=False);k45=BoolProperty(name='',default=False)
    k46=BoolProperty(name='',default=False);k47=BoolProperty(name='',default=False)
    rotationPropX=IntProperty(name='',min=0,max=360,default= 0,description='Window Rotation X')
    rotationPropY=IntProperty(name='',min=0,max=360,default= 0,description='Window Rotation Y')
    rotationPropZ=IntProperty(name='',min=0,max=360,default= 0,description='Window Rotation Z')
    locationPropX=FloatProperty(name='',min=-10000,max=10000,default= 0,description='Window Location X')
    locationPropY=FloatProperty(name='',min=-10000,max=10000,default= 0,description='Window Location Y')
    locationPropZ=FloatProperty(name='',min=-10000,max=10000,default= 0,description='Window Location Z')
    #--------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        layout.prop(self,'prs')
        box=layout.box()
        box.prop(self,'gen');box.prop(self,'yuk')
        box.prop(self,'kl1');box.prop(self,'kl2')
        box.prop(self, 'fk')

        box.prop(self,'mr')
        if  self.mr==True:
            row=box.row();row.prop(self,'mr1');row.prop(self,'mr2')
            row=box.row();row.prop(self,'mr3');row.prop(self,'mr4')
        row =layout.row();row.label('Frame');row.label('Inner Frame')
        row =layout.row();row.prop(self,'mt1');row.prop(self,'mt2')

        box.prop(self,'UST')
        if   self.UST=='2':
            row= box.row();    row.prop(self,'DT2')
            if   self.DT2=='1':row.prop(self,'VL1')
            elif self.DT2=='2':row.prop(self,'VL2')
            box.prop(self,'RES')
        elif self.UST=='3':
            row= box.row();    row.prop(self,'DT3')
            if   self.DT3=='1':row.prop(self,'VL1')
            elif self.DT3=='2':row.prop(self,'VL3')
            elif self.DT3=='3':row.prop(self,'VL4')
        elif self.UST=='4':
            row= box.row();    row.prop(self,'DT3')
            if   self.DT3=='1':row.prop(self,'VL1')
            elif self.DT3=='2':row.prop(self,'VL3')
            elif self.DT3=='3':row.prop(self,'VL4')
        row =layout.row()
        for i in range(0,self.gen):
            row.prop(self,'gnx'+str(i))
        for j in range(0,self.yuk):
            row=layout.row()
            row.prop(self,'gny'+str(self.yuk-j-1))
            for i in range(0,self.gen):
                row.prop(self,'k'+str(self.yuk-j-1)+str(i))
        row =layout.row()
        box.row();row.label('X');row.label('Y');row.label('Z')
        row =layout.row()
        row.label("Rotation")
        row =layout.row()
        box.row();row.prop(self,'rotationPropX');row.prop(self,'rotationPropY');row.prop(self,'rotationPropZ')
        row =layout.row()
        row.label("Location")
        row =layout.row()
        box.row();row.prop(self,'locationPropX');row.prop(self,'locationPropY');row.prop(self,'locationPropZ')

    def execute(self, context):
        if self.son!=self.prs:
            Prs(self)
            self.son=self.prs
        name = add_object(self,context)
        bpy.data.objects[name].rotation_euler[0] = radians(self.rotationPropX)
        bpy.data.objects[name].rotation_euler[1] = radians(self.rotationPropY)
        bpy.data.objects[name].rotation_euler[2] = radians(self.rotationPropZ)
        bpy.data.objects[name].location[0] = bpy.context.scene.cursor_location[0] + self.locationPropX
        bpy.data.objects[name].location[1] = bpy.context.scene.cursor_location[1] + self.locationPropY
        bpy.data.objects[name].location[2] = bpy.context.scene.cursor_location[2] + self.locationPropZ
        return {'FINISHED'}
