"""
SVG 2 OBJ translater, 0.2.7
(c) jm soler juillet/novembre 2004, released under Blender Artistic Licence 
    for the Blender 2.34/33 Python Scripts Bundle.
#---------------------------------------------------------------------------
# Page officielle :
#   http://jmsoler.free.fr/didacticiel/blender/tutor/cpl_import_svg.htm
# Communiquer les problemes et erreurs sur:
#   http://www.zoo-logique.org/3D.Blender/newsportal/thread.php?group=3D.Blender
#---------------------------------------------------------------------------

-- Concept : translate SVG file in GEO .obj file and try to load it. 
-- Curiousity : the original matrix must be :

                         0.0 0.0 1.0 0.0
                         0.0 1.0 0.0 0.0
                         0.0 0.0 1.0 0.0
                         0.0 0.0 0.0 1.0 

                  and not:
                         1.0 0.0 0.0 0.0
                         0.0 1.0 0.0 0.0
                         0.0 0.0 1.0 0.0
                         0.0 0.0 0.0 1.0 

-- Options :
    SHARP_IMPORT = 0 
            choise between "As is", "Devide by height" and "Devide by width"
    SHARP_IMPORT = 1
            no choise

-- Possible bug : sometime, the new curves object's RotY value 
                  jumps to -90.0 degrees without any reason.

Yet done: 
   M : absolute move to 
   Z : close path
   L : absolute line to  
   C : absolute curve to
   S : absolute curve to with only one handle
   l : relative line to     2004/08/03
   c : relative curve to    2004/08/03
   s : relative curve to with only one handle  


   A : courbe_vers_a, 
   V : ligne_tracee_v,
   H : ligne_tracee_h, 
   Z : boucle_z,
   Q : courbe_vers_q,
   T : courbe_vers_t,
   a : courbe_vers_a, 
   v : ligne_tracee_v,
   h : ligne_tracee_h, 
   z : boucle_z,
   q : courbe_vers_q,
	

Changelog:
      0.1.1 : - control file without extension
      0.2.0 : - improved reading of several data of the same type 
                following the same command (for gimp import)
      0.2.1 : - better choice for viewboxing ( takes the viewbox if found, 
                instead of x,y,width and height              
      0.2.2 : - read compact path data from Illustrator 10             
      0.2.3 : - read a few new relative displacements
      0.2.4 : - better hash for command followed by a lone data 
                (h,v) or uncommun number (a) 
      0.2.5 : - correction for gimp import 
      0.2.6 : - correction for illustrator 10 SVG
      0.2.7 : - correction for inskape 0.40 cvs  SVG
      0.2.8 : - correction for inskape plain SVG

                
==================================================================================   
=================================================================================="""

SHARP_IMPORT=0
SCALE=1
scale=1
DEBUG =0 #print
DEVELOPPEMENT=0
    
import sys
#oldpath=sys.path
import Blender
BLversion=Blender.Get('version')

try:
    import nt
    os=nt
    os.sep='\\'

except:    
    import posix
    os=posix
    os.sep='/'
    
def isdir(path):
    try:
        st = os.stat(path)
        return 1 
    except:
        return 0
    
def split(pathname):
         if pathname.find(os.sep)!=-1:
             k0=pathname.split(os.sep)
         else:
            if os.sep=='/':
                k0=pathname.split('\\')
            else:
                k0=pathname.split('/') 

         directory=pathname.replace(k0[len(k0)-1],'')
         Name=k0[len(k0)-1]
         return directory, Name
        
def join(l0,l1):        
     return  l0+os.sep+l1
    
os.isdir=isdir
os.split=split
os.join=join

def filtreFICHIER(nom):
     f=open(nom,'rU')
     t=f.read()
     f.close()
     
     t=t.replace('\r','')
     t=t.replace('\n','')
     
     if t.upper().find('<SVG')==-1 :
         name = "ERROR: invalid or empty file ... "  # if no %xN int is set, indices start from 1
         result = Blender.Draw.PupMenu(name)
         return "false"
     elif  t.upper().find('<PATH')==-1:
         name = "ERROR: there's no Path in this file ... "  # if no %xN int is set, indices start from 1
         result = Blender.Draw.PupMenu(name)
         return "false"
     else:
          return t

#===============================
# Data
#===============================
#===============================
# Blender Curve Data
#===============================
objBEZIER=0
objSURFACE=5
typBEZIER3D=1  #3D
typBEZIER2D=9  #2D

class Bez:
      def __init__(self):
           self.co=[]
           self.ha=[0,0]
           
class ITEM:
      def __init__(self):
               self.type        =  typBEZIER3D,        
               self.pntsUV      =  [0,0]              
               self.resolUV     =  [32,0]            
               self.orderUV     =  [0,0]             
               self.flagUV      =  [0,0]              
               self.Origine     =  [0.0,0.0]
               self.beziers_knot = []

class COURBE:
      def __init__(self):
              self.magic_number='3DG3'              
              self.type            =  objBEZIER        
              self.number_of_items =  0              
              self.ext1_ext2       =  [0,0]             
              self.matrix          =  """0.0 0.0 1.0 0.0
0.0 1.0 0.0 0.0
0.0 0.0 1.0 0.0
0.0 0.0 0.0 1.0 """ 
              self.ITEM = {}


courbes=COURBE()
PATTERN={}
BOUNDINGBOX={'rec':[],'coef':1.0}
npat=0
#=====================================================================
#======== name of the curve in the curves dictionnary ===============
#=====================================================================
n0=0

#=====================================================================
#====================== current Point ================================
#=====================================================================
CP=[0.0,0.0] #currentPoint

#=====================================================================
#===== to compare last position to the original move to displacement =
#=====  needed for cyclic definition inAI, EPS forma  ================
#=====================================================================
def test_egalitedespositions(f1,f2):
    if f1[0]==f2[0] and f1[1]==f2[1]:
       return Blender.TRUE
    else:
       return Blender.FALSE


def Open_GEOfile(dir,nom):
    global SCALE,BOUNDINGBOX, scale
    if BLversion>=233:
       Blender.Load(dir+nom+'OOO.obj', 1)
       BO=Blender.Object.Get()

       BO[-1].RotY=3.1416
       BO[-1].RotZ=3.1416
       BO[-1].RotX=3.1416/2.0
       
       if scale==1:
          BO[-1].LocY+=BOUNDINGBOX['rec'][3]
       else:
         BO[-1].LocY+=BOUNDINGBOX['rec'][3]/SCALE
 
       BO[-1].makeDisplayList() 
       Blender.Window.RedrawAll()
    else:
       print "Not yet implemented"

def create_GEOtext(courbes):
    global SCALE, B, BOUNDINGBOX,scale
    r=BOUNDINGBOX['rec']

    if scale==1:
       SCALE=1.0
    elif scale==2:
       SCALE=r[2]-r[0]
    elif scale==3:
       SCALE=r[3]-r[1]
 
    t=[]
    t.append(courbes.magic_number+'\n')
    t.append(str(courbes.type)+'\n')
    t.append(str(courbes.number_of_items)+'\n')
    t.append(str(courbes.ext1_ext2[0])+' '+str(courbes.ext1_ext2[1])+'\n')
    t.append(courbes.matrix+'\n')
    
    for k in courbes.ITEM.keys():
        t.append("%s\n"%courbes.ITEM[k].type)
        t.append("%s %s \n"%(courbes.ITEM[k].pntsUV[0],courbes.ITEM[k].pntsUV[1]))
        t.append("%s %s \n"%(courbes.ITEM[k].resolUV[0],courbes.ITEM[k].resolUV[1]))
        t.append("%s %s \n"%(courbes.ITEM[k].orderUV[0],courbes.ITEM[k].orderUV[1]))
        t.append("%s %s \n"%(courbes.ITEM[k].flagUV[0],courbes.ITEM[k].flagUV[1]))

        flag =0#courbes.ITEM[k].flagUV[0]

        for k2 in range(flag,len(courbes.ITEM[k].beziers_knot)):
           #k1 =courbes.ITEM[k].beziers_knot[k2]
           k1=ajustement(courbes.ITEM[k].beziers_knot[k2], SCALE)
           
           t.append("%4f 0.0 %4f \n"%(k1[4],k1[5]))
           t.append("%4f 0.0 %4f \n"%(k1[0],k1[1]))
           t.append("%4f 0.0 %4f \n"%(k1[2],k1[3]))
           t.append(str(courbes.ITEM[k].beziers_knot[k2].ha[0])+' '+str(courbes.ITEM[k].beziers_knot[k2].ha[1])+'\n')

    return t

def save_GEOfile(dir,nom,t):
     f=open(dir+nom+'OOO.obj','w')
     f.writelines(t)
     f.close()
     #warning = "REMINDER : %t | Do not forget to rename your blender file NOW ! %x1"
     #result = Blender.Draw.PupMenu(warning)


def filtre_DATA(c,D,n):
    global DEBUG,TAGcourbe
    l=[] 

    if len(c[0])==1 and D[c[1]+1].find(',')!=-1:
        for n2 in range(1,n+1): 
           ld=D[c[1]+n2].split(',')
           for l_ in ld: 
               l.append(l_)
               
    elif len(c[0])==1 and D[c[1]+2][0] not in  TAGcourbe:
        for n2 in range(1,n*2+1):
           l.append(D[c[1]+n2])
        if DEBUG==1 : print l 

    return l

#=====================================================================
#=====      SVG format   :  DEBUT             =========================
#=====================================================================

def contruit_SYMETRIC(l):
    L=[float(l[0]), float(l[1]),
       float(l[2]),float(l[3])]
    X=L[0]-(L[2]-L[0])
    Y=L[1]-(L[3]-L[1])
    l =[l[0],l[1],"%4s"%X,"%4s"%Y,l[2],l[3]]   
    return l

def mouvement_vers(c, D, n0,CP):
    global DEBUG,TAGcourbe
    print 'c',c,'D[c[1]+1]',D[c[1]+1]

    l=filtre_DATA(c,D,1)
    print 'l',l
    if n0 in courbes.ITEM.keys():
       n0+=1
    #
    #   CP=[l[0],l[1]]        
    #else:
    #   CP=[l[0],l[1]] 
    CP=[l[0],l[1]] 

    courbes.ITEM[n0]=ITEM() 
    courbes.ITEM[n0].Origine=[l[0],l[1]] 

    B=Bez()
    B.co=[CP[0],CP[1],CP[0],CP[1],CP[0],CP[1]]
    B.ha=[0,0]
    
    courbes.ITEM[n0].beziers_knot.append(B)
    if DEBUG==1: print courbes.ITEM[n0], CP
    

    return  courbes,n0,CP     
    
def boucle_z(c,D,n0,CP): #Z,z
    #print c, 'close'
    courbes.ITEM[n0].flagUV[0]=1 
    return  courbes,n0,CP    
   
def courbe_vers_s(c,D,n0,CP):  #S,s
    l=filtre_DATA(c,D,2) 
    if c[0]=='s':
       l=["%4s"%(float(l[0])+float(CP[0])),
          "%4s"%(float(l[1])+float(CP[1])),
          "%4s"%(float(l[2])+float(CP[0])),
          "%4s"%(float(l[3])+float(CP[1]))]
    l=contruit_SYMETRIC(l)    
    B=Bez()
    B.co=[l[4],l[5],l[2],l[3],l[0],l[1]] #plus toucher au 2-3
    B.ha=[0,0]

    BP=courbes.ITEM[n0].beziers_knot[-1]
    BP.co[2]=l[2]  #4-5 point prec
    BP.co[3]=l[3]

    courbes.ITEM[n0].beziers_knot.append(B)
    if DEBUG==1: print B.co,BP.co
    CP=[l[4],l[5]]    

    if len(D)<c[1]+3 and D[c[1]+3] not in TAGcourbe :
        c[1]+=2
        courbe_vers_c(c, D, n0,CP)
    return  courbes,n0,CP

def courbe_vers_a(c,D,n0,CP):  #A
    #print c
    return  courbes,n0,CP     

def courbe_vers_q(c,D,n0,CP):  #Q
    #print c
    return  courbes,n0,CP     

def courbe_vers_t(c,D,n0,CP):  #T
    return  courbes,n0,CP     
       
def courbe_vers_c(c, D, n0,CP): #c,C

    l=filtre_DATA(c,D,3) 
    #print l, c, CP

    if c[0]=='c':
       l=["%4s"%(float(l[0])+float(CP[0])),
          "%4s"%(float(l[1])+float(CP[1])),
          "%4s"%(float(l[2])+float(CP[0])),
          "%4s"%(float(l[3])+float(CP[1])),
          "%4s"%(float(l[4])+float(CP[0])),
          "%4s"%(float(l[5])+float(CP[1]))]

    #print l
   
    B=Bez()
    B.co=[l[4],
          l[5],
          l[0],
          l[1],
          l[2],
          l[3]] #plus toucher au 2-3

    B.ha=[0,0]

    BP=courbes.ITEM[n0].beziers_knot[-1]

    BP.co[2]=l[0]
    BP.co[3]=l[1]

    courbes.ITEM[n0].beziers_knot.append(B)
    if DEBUG==1: print B.co,BP.co

    CP=[l[4],l[5]]
    if DEBUG==1:
       print 'D[c[1]]', D[c[1]], c
       print D
    if len(D)<c[1]+4 and D[c[1]+4] not in TAGcourbe :
        c[1]+=3
        courbe_vers_c(c, D, n0,CP)

    return  courbes,n0,CP
    
    
def ligne_tracee_l(c, D, n0,CP): #L,l
    #print c
    
    l=filtre_DATA(c,D,1)
    if c[0]=='l':
       l=["%4s"%(float(l[0])+float(CP[0])),
          "%4s"%(float(l[1])+float(CP[1]))]

    B=Bez()
    B.co=[l[0],l[1],l[0],l[1],l[0],l[1]]
    B.ha=[0,0]
    courbes.ITEM[n0].beziers_knot.append(B)    

    CP=[l[0],l[1]]

    if len(D)<c[1]+2 and D[c[1]+2] not in TAGcourbe :
        c[1]+=1
        ligne_tracee_l(c, D, n0,CP) #L
            
    return  courbes,n0,CP    
    
    
def ligne_tracee_h(c,D,n0,CP): #H,h
         
    return  courbes,n0,CP    

def ligne_tracee_v(c,D,n0,CP): #V
    #print c
    #CP=[]
    return  courbes,n0,CP    

def boucle_tracee_z(c,D,n0,CP): #Z
    #print c
    #CP=[]
    return  courbes,n0,CP    
     
Actions=   {     "C" : courbe_vers_c,
                 "A" : courbe_vers_a, 
                 "S" : courbe_vers_s,
                 "M" : mouvement_vers,
                 "V" : ligne_tracee_v,
                 "L" : ligne_tracee_l,
                 "H" : ligne_tracee_h,                
                 "Z" : boucle_z,
                 "Q" : courbe_vers_q,
                 "T" : courbe_vers_t,

                 "c" : courbe_vers_c,
                 "a" : courbe_vers_a, 
                 "s" : courbe_vers_s,
                 "m" : mouvement_vers,
                 "v" : ligne_tracee_v,
                 "l" : ligne_tracee_l,
                 "h" : ligne_tracee_h,                
                 "z" : boucle_z,
                 "q" : courbe_vers_q,
                 "T" : courbe_vers_t
}
     
TAGcourbe=Actions.keys()

def get_content(val,t0):
    t=t0[:] 
    if t.find(' '+val+'="')!=-1:
       t=t[t.find(' '+val+'="')+len(' '+val+'="'):]
       val=t[:t.find('"')]
       t=t[t.find('"'):]
       #----------------------------------------------------------------
       #print t[:10], val
       #wait=raw_input('wait:'  )

       return t0,val
    else:
       return t0,0

def get_tag(val,t):

    t=t[t.find('<'+val):]
    val=t[:t.find('>')+1]
    t=t[t.find('>')+1:]
    
    if DEBUG==3 : print t[:10], val

    return t,val
    
def get_val(val,t):
    d=""
    #print t
    for l in t:
        if l.find(val+'="')!=-1:
            #print 'l', l
            # 0.2.7 : - correction for inskape 0.40 cvs  SVG
            l=l.replace('>','')
            # 0.2.7 : -- end 
            d=l[l[:-1].rfind('"')+1:-1]
            #print 'd', d   
            for nn in d:
                if '0123456789.'.find(nn)==-1:
                     d=d.replace(nn,"")
                     #print d
            d=float(d)
            break
        #else:
	    #  print l
        d=0.0 
    return d

def get_BOUNDBOX(BOUNDINGBOX,SVG,viewbox):
    if viewbox==0:
        h=get_val('height',SVG)
        print 'h : ',h
        w=get_val('width',SVG)
        print 'w :',w
        BOUNDINGBOX['rec']=[0.0,0.0,w,h]
        r=BOUNDINGBOX['rec']
        BOUNDINGBOX['coef']=w/h       
    else:
        viewbox=viewbox.split()
        BOUNDINGBOX['rec']=[float(viewbox[0]),float(viewbox[1]),float(viewbox[2]),float(viewbox[3])]
        r=BOUNDINGBOX['rec']
        BOUNDINGBOX['coef']=(r[2]-r[0])/(r[3]-r[1])       

    return BOUNDINGBOX

# 0.2.8 : - correction for inskape 0.40 cvs  SVG
def repack_DATA(DATA):   
    for d in Actions.keys():
        DATA=DATA.replace(d,d+' ')
    return DATA    


def unpack_DATA(DATA):
    DATA[0]=DATA[0].replace('-',',-')
    
    for d in Actions.keys():
        DATA[0]=DATA[0].replace(d,','+d+',')

    DATA[0]=DATA[0].replace(',,',',')
    if DATA[0][0]==',':DATA[0]=DATA[0][1:]
    if DATA[0][-1]==',':DATA[0]=DATA[0][:-1]
    DATA[0]=DATA[0].replace('\n','')
    DATA[0]=DATA[0].replace('\t','')
    DATA[0]=DATA[0].split(',')
    D2=[]
    D1=DATA[0]
    
    for cell in range(len(D1)):
       if D1[cell] in Actions.keys():
          D2.append(D1[cell])
          n=1
          if D1[cell] not in ['h','v','H','V','a','A']:
              while cell+n+1<len(D1) and (D1[cell+n] not in  Actions.keys()):
                 D2.append(D1[cell+n]+','+D1[cell+n+1])               
                 n+=2
          elif D1[cell] in ['h','v','H','V']:       
              while cell+n+1<len(D1) and (D1[cell+n] not in  Actions.keys()):
                 D2.append(D1[cell+n])
                 n+=1
          elif D1[cell] in ['a','A']:       
                 #(rx ry rotation-axe-x drapeau-arc-large drapeau-balayage x y)
                 #150,150 0 1,0 150,-150
                 D2.append(D1[cell+n]+','+D1[cell+n+1])
                 D2.append(D1[cell+n+2])
                 D2.append(D1[cell+n+3]+','+D1[cell+n+4])
                 D2.append(D1[cell+n+5]+','+D1[cell+n+6])
                 n+=7
    return D2

def format_PATH(t):

    t,PATH=get_tag('path',t)

    if PATH.find(' id="')!=-1:
       PATH,ID=get_content('id',PATH)
       #print 'ident = ', ID

    if PATH.find(' STROKE="')!=-1:
       PATH,ID=get_content('stroke',PATH)
       #print 'path stroke = ', ID

    if PATH.find(' stroke-width="')!=-1:
       PATH,ID=get_content('stroke-width',PATH)
       #print 'path stroke-width = ', ID

    if PATH.find(' d="')!=-1:
       PATH,D=get_content('d',PATH)

    # 0.2.8 : - correction for inskape plain SVG    
    if D.find(',')==-1:
        D=repack_DATA(D)
    # 0.2.8 : end
        
    D=D.split(' ')
    
    try:
      while D.index(''):
         del D[D.index('')]
    except:
      pass
    
    if len(D)==1 or len(D[0])>1:
       D1=[]     
       for D0 in D:
           D1+=unpack_DATA([D0])[:]
       D=D1
       
    return t,D


def scan_FILE(nom):
  global CP, courbes, SCALE, DEBUG, BOUNDINGBOX, scale
  dir,name=split(nom)
  name=name.split('.')
  n0=0
  result=0
  
  t=filtreFICHIER(nom)
  
  if t!='false':
     if not SHARP_IMPORT:
         warning = "Select Size : %t| As is %x1 | Scale on Height %x2| Scale on Width %x3" 
         scale = Blender.Draw.PupMenu(warning)
     npat=0
     l=0
     do=0
     t,SVG=get_tag('svg',t)

     SVG,viewbox=get_content('viewBox',SVG)

     SVG=SVG.split(' ')
     print SVG
     if viewbox==0:
          BOUNDINGBOX = get_BOUNDBOX(BOUNDINGBOX,SVG,0)
     else:
          BOUNDINGBOX = get_BOUNDBOX(BOUNDINGBOX,SVG,viewbox)     

     while t.find('path')!=-1:
         t,D=format_PATH(t)
         cursor=0
         for cell in D: 
            if DEBUG==2 : print 'cell : ',cell ,' --'                   
            if len(cell)>=1 and cell[0] in TAGcourbe:
                   courbes,n0,CP=Actions[cell]([cell,cursor], D, n0,CP)            
            cursor+=1

  courbes.number_of_items=len(courbes.ITEM.keys())

  for k in courbes.ITEM.keys():
     courbes.ITEM[k].pntsUV[0] =len(courbes.ITEM[k].beziers_knot)

  if courbes.number_of_items>0:
     if len(PATTERN.keys() )>0:
        if DEBUG == 3 : print len(PATTERN.keys() )
     t=create_GEOtext(courbes)
     save_GEOfile(dir,name[0],t)
     Open_GEOfile(dir,name[0])
  else:
      pass
    
def  ajustement(v,s):
     
     a,b,c,d,e,f=float(v.co[0]),float(v.co[1]),float(v.co[2]),float(v.co[3]),float(v.co[4]),float(v.co[5])
     return [a/s,-b/s,c/s,-d/s,e/s,-f/s]

#=====================================================================
#====================== SVG format mouvements ========================
#=====================================================================

#=====================================================================
# une sorte de contournement qui permet d'utiliser la fonction
# et de documenter les variables Window.FileSelector
#=====================================================================
def fonctionSELECT(nom):
    scan_FILE(nom)

if DEVELOPPEMENT==1:
   Blender.Window.FileSelector (fonctionSELECT, 'SELECT a .SVG FILE')
