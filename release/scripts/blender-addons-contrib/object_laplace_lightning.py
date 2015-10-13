# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
bl_info = {
    "name": "Laplacian Lightning",
    "author": "teldredge",
    "version": (0, 2, 7),
    "blender": (2, 71, 0),
    "location": "View3D > Toolshelf > Create Tab",
    "description": "Lightning mesh generator using laplacian growth algorithm",
    "warning": "Beta",
    "wiki_url": "http://www.funkboxing.com/wordpress/?p=301",
    "tracker_url": "https://developer.blender.org/maniphest/task/create/?project=3&type=Bug",
    "category": "Object"}
        
######################################################################
######################################################################
##################### BLENDER LAPLACIAN LIGHTNING ####################
############################ teldredge ###############################
######################## www.funkboxing.com ##########################
################# https://developer.blender.org/T27189 ###############
######################################################################
######################## using algorithm from ########################
######################################################################
############## FAST SIMULATION OF LAPLACIAN GROWTH (FSLG) ############
#################### http://gamma.cs.unc.edu/FRAC/ ###################
######################################################################
###################### and a few ideas ideas from ####################
######################################################################
##### FAST ANIMATION OF LIGHTNING USING AN ADAPTIVE MESH (FALUAM) ####
################ http://gamma.cs.unc.edu/FAST_LIGHTNING/ #############
######################################################################
######################################################################
"""           -----RELEASE LOG/NOTES/PONTIFICATIONS-----
v0.1.0 - 04.11.11
    basic generate functions and UI
    object creation report (Custom Properties: FSLG_REPORT)
v0.2.0 - 04.15.11
    started spelling laplacian right.
    add curve function (not in UI) ...twisting problem
    classify stroke by MAIN path, h-ORDER paths, TIP paths
    jitter cells for mesh creation
    add materials if present
v0.2.1 - 04.16.11
    mesh classification speedup
v0.2.2 - 04.21.11
    fxns to write/read array to file 
    restrict growth to insulator cells (object bounding box)
    origin/ground defineable by object
    gridunit more like 'resolution'
v0.2.3 - 04.24.11
    cloud attractor object (termintates loop if hit)
    secondary path orders (hOrder) disabled in UI (set to 1)
v0.2.4 - 04.26.11
    fixed object selection in UI
    will not run if required object not selected   
    moved to view 3d > toolbox
v0.2.5 - 05.08.11
    testing for 2.57b
    single mesh output (for build modifier)
    speedups (dist fxn)
v0.2.6 - 06.20.11
    scale/pos on 'write to cubes' works now
    if origin obj is mesh, uses all verts as initial charges
    semi-helpful tooltips
    speedups, faster dedupe fxn, faster classification
    use any shape mesh obj as insulator mesh
        must have rot=0, scale=1, origin set to geometry
        often fails to block bolt with curved/complex shapes
    separate single and multi mesh creation
v0.2.7 - 01.05.13
    fixed the issue that prevented enabling the add-on
    fixed makeMeshCube fxn
    disabled visualization for voxels

v0.x -
    -prevent create_setup_objects from generating duplicates
    -fix vis fxn to only buildCPGraph once for VM or VS
    -improve list fxns (rid of ((x,y,z),w) and use (x,y,z,w)), use 'sets'
    -create python cmodule for a few of most costly fxns
        i have pretty much no idea how to do this yet
    -cloud and insulator can be groups of MESH objs
    -text output, possibly to save on interrupt, allow continue from text
    -?hook modifiers from tips->sides->main, weight w/ vert groups
    -user defined 'attractor' path
    -fix add curve function
    -animated arcs via. ionization path    
    -environment map boundary conditions - requires Eqn. 15 from FSLG.
    -assign wattage at each segment for HDRI
    -?default settings for -lightning, -teslacoil, -spark/arc
    -fix hOrder functionality
    -multiple 'MAIN' brances for non-lightning discharges
    -n-symmetry option, create mirror images, snowflakes, etc...
"""

######################################################################
######################################################################
######################################################################
import bpy
import time
import random
from math import sqrt
from mathutils import Vector
import struct
import bisect
import os.path
notZero = 0.0000000001
#scn = bpy.context.scene
winmgr = bpy.context.window_manager

######################################################################
########################### UTILITY FXNS #############################
######################################################################
def within(x,y,d):
###---CHECK IF x-d <= y <= x+d
    if x-d <= y and x + d >= y:
        return True
    else: return False

def dist(ax, ay, az ,bx, by, bz):
    dv = Vector((ax,ay,az)) - Vector((bx,by,bz))
    d = dv.length
    return d

def splitList(aList, idx):
    ll = []
    for x in aList:
        ll.append(x[idx])
    return ll

def splitListCo(aList):
    ll = []
    for p in aList:
        ll.append((p[0], p[1], p[2]))
    return ll

def getLowHigh(aList):
    tLow = aList[0]; tHigh = aList[0]
    for a in aList:
        if a < tLow: tLow = a
        if a > tHigh: tHigh = a
    return tLow, tHigh

def weightedRandomChoice(aList):
    tL = []
    tweight = 0
    for a in range(len(aList)):
        idex = a; weight = aList[a]
        if weight > 0.0:
            tweight += weight
            tL.append((tweight, idex))
    i = bisect.bisect(tL, (random.uniform(0, tweight), None))    
    r = tL[i][1]
    return r

def getStencil3D_26(x,y,z):
    nL = []
    for xT in range(x-1, x+2):
        for yT in range(y-1, y+2):
            for zT in range(z-1, z+2):
                nL.append((xT, yT, zT))
    nL.remove((x,y,z))
    return nL

def jitterCells(aList, jit):
    j = jit/2
    bList = []
    for a in aList:
        ax = a[0] + random.uniform(-j, j)
        ay = a[1] + random.uniform(-j, j)
        az = a[2] + random.uniform(-j, j)
        bList.append((ax, ay, az))
    return bList

def deDupe(seq, idfun=None): 
###---THANKS TO THIS GUY - http://www.peterbe.com/plog/uniqifiers-benchmark
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

######################################################################
######################## VISUALIZATION FXNS ##########################
######################################################################
def writeArrayToVoxel(arr, filename):
    gridS = 64
    half = int(gridS/2)
    bitOn = 255
    aGrid = [[[0 for z in range(gridS)] for y in range(gridS)] for x in range(gridS)]
    for a in arr:
        try:
            aGrid[a[0]+half][a[1]+half][a[2]+half] = bitOn
        except:
            print('Particle beyond voxel domain')
    file = open(filename, "wb")
    for z in range(gridS):
        for y in range(gridS):
            for x in range(gridS):
                file.write(struct.pack('B', aGrid[x][y][z]))
    file.flush()
    file.close()
        
def writeArrayToFile(arr, filename):
    file = open(filename, "w")
    for a in arr:
        tstr = str(a[0]) + ',' + str(a[1]) + ',' + str(a[2]) + '\n'
        file.write(tstr)
    file.close

def readArrayFromFile(filename):
    file = open(filename, "r")
    arr = []
    for f in file:
        pt = f[0:-1].split(',')
        arr.append((int(pt[0]), int(pt[1]), int(pt[2])))
    return arr

def makeMeshCube_OLD(msize):
    msize = msize/2
    mmesh = bpy.data.meshes.new('q')
    mmesh.vertices.add(8)
    mmesh.vertices[0].co = [-msize, -msize, -msize]
    mmesh.vertices[1].co = [-msize,  msize, -msize]
    mmesh.vertices[2].co = [ msize,  msize, -msize]
    mmesh.vertices[3].co = [ msize, -msize, -msize]
    mmesh.vertices[4].co = [-msize, -msize,  msize]
    mmesh.vertices[5].co = [-msize,  msize,  msize]
    mmesh.vertices[6].co = [ msize,  msize,  msize]
    mmesh.vertices[7].co = [ msize, -msize,  msize]
    mmesh.faces.add(6)
    mmesh.faces[0].vertices_raw = [0,1,2,3]
    mmesh.faces[1].vertices_raw = [0,4,5,1]
    mmesh.faces[2].vertices_raw = [2,1,5,6]
    mmesh.faces[3].vertices_raw = [3,2,6,7]
    mmesh.faces[4].vertices_raw = [0,3,7,4]
    mmesh.faces[5].vertices_raw = [5,4,7,6]
    mmesh.update(calc_edges=True)
    return(mmesh)

def makeMeshCube(msize):
    m2 = msize/2
    #verts = [(0,0,0),(0,5,0),(5,5,0),(5,0,0),(0,0,5),(0,5,5),(5,5,5),(5,0,5)]
    verts = [(-m2,-m2,-m2),(-m2,m2,-m2),(m2,m2,-m2),(m2,-m2,-m2),
             (-m2,-m2,m2),(-m2,m2,m2),(m2,m2,m2),(m2,-m2,m2)]
    faces = [(0,1,2,3), (4,5,6,7), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]
 
    #Define mesh and object
    mmesh = bpy.data.meshes.new("Cube")
    #mobject = bpy.data.objects.new("Cube", mmesh)
 
    #Set location and scene of object
    #mobject.location = bpy.context.scene.cursor_location
    #bpy.context.scene.objects.link(mobject)
 
    #Create mesh
    mmesh.from_pydata(verts,[],faces)
    mmesh.update(calc_edges=True)
    return(mmesh)

def writeArrayToCubes(arr, gridBU, orig, cBOOL = False, jBOOL = True):
    for a in arr:
        x = a[0]; y = a[1]; z = a[2]
        me = makeMeshCube(gridBU)
        ob = bpy.data.objects.new('xCUBE', me)
        ob.location.x = (x*gridBU) + orig[0]
        ob.location.y = (y*gridBU) + orig[1]
        ob.location.z = (z*gridBU) + orig[2]
        if cBOOL: ###---!!!MOSTLY UNUSED
            ###   POS+BLUE, NEG-RED, ZERO:BLACK
            col = (1.0, 1.0, 1.0, 1.0)
            if a[3] == 0: col = (0.0, 0.0, 0.0, 1.0)
            if a[3] < 0: col = (-a[3], 0.0, 0.0, 1.0)
            if a[3] > 0: col = (0.0, 0.0, a[3], 1.0)                
            ob.color = col
        bpy.context.scene.objects.link(ob)
        bpy.context.scene.update()
    if jBOOL:
        ###---SELECTS ALL CUBES w/ ?bpy.ops.object.join() b/c
        ###   CAN'T JOIN ALL CUBES TO A SINGLE MESH RIGHT... ARGH...
        for q in bpy.context.scene.objects:
            q.select = False
            if q.name[0:5] == 'xCUBE':
                q.select = True
                bpy.context.scene.objects.active = q

def addVert(ob, pt, conni = -1):
    mmesh = ob.data
    mmesh.vertices.add(1)
    vcounti = len(mmesh.vertices)-1
    mmesh.vertices[vcounti].co = [pt[0], pt[1], pt[2]]
    if conni > -1:
        mmesh.edges.add(1)
        ecounti = len(mmesh.edges)-1
        mmesh.edges[ecounti].vertices = [conni, vcounti]
        mmesh.update()

def addEdge(ob, va, vb):
    mmesh = ob.data
    mmesh.edges.add(1)
    ecounti = len(mmesh.edges)-1
    mmesh.edges[ecounti].vertices = [va, vb]
    mmesh.update()    

def newMesh(mname):
    mmesh = bpy.data.meshes.new(mname)
    omesh = bpy.data.objects.new(mname, mmesh)
    bpy.context.scene.objects.link(omesh)
    return omesh      

def writeArrayToMesh(mname, arr, gridBU, rpt = None):
    mob = newMesh(mname)
    mob.scale = (gridBU, gridBU, gridBU)
    if rpt: addReportProp(mob, rpt)
    addVert(mob, arr[0], -1)
    for ai in range(1, len(arr)):
        a = arr[ai]
        addVert(mob, a, ai-1)
    return mob        

###---!!!OUT OF ORDER - SOME PROBLEM WITH IT ADDING (0,0,0)
def writeArrayToCurves(cname, arr, gridBU, bd = .05, rpt = None):
    cur = bpy.data.curves.new('fslg_curve', 'CURVE')
    cur.use_fill_front = False
    cur.use_fill_back = False    
    cur.bevel_depth = bd
    cur.bevel_resolution = 2    
    cob = bpy.data.objects.new(cname, cur)
    cob.scale = (gridBU, gridBU, gridBU)
    if rpt: addReportProp(cob, rpt)
    bpy.context.scene.objects.link(cob)
    cur.splines.new('BEZIER')
    cspline = cur.splines[0]
    div = 1 ###   SPACING FOR HANDLES (2 - 1/2 WAY, 1 - NEXT BEZIER)
    for a in range(len(arr)):
        cspline.bezier_points.add(1)
        bp = cspline.bezier_points[len(cspline.bezier_points)-1]
        if a-1 < 0: hL = arr[a]
        else:
            hx = arr[a][0] - ((arr[a][0]-arr[a-1][0]) / div)
            hy = arr[a][1] - ((arr[a][1]-arr[a-1][1]) / div)
            hz = arr[a][2] - ((arr[a][2]-arr[a-1][2]) / div)
            hL = (hx,hy,hz)
        
        if a+1 > len(arr)-1: hR = arr[a]
        else:
            hx = arr[a][0] + ((arr[a+1][0]-arr[a][0]) / div)
            hy = arr[a][1] + ((arr[a+1][1]-arr[a][1]) / div)
            hz = arr[a][2] + ((arr[a+1][2]-arr[a][2]) / div)
            hR = (hx,hy,hz)
        bp.co = arr[a]
        bp.handle_left = hL
        bp.handle_right = hR

def addArrayToMesh(mob, arr):
    addVert(mob, arr[0], -1)
    mmesh = mob.data
    vcounti = len(mmesh.vertices)-1
    for ai in range(1, len(arr)):
        a = arr[ai]
        addVert(mob, a, len(mmesh.vertices)-1)

def addMaterial(ob, matname):
    mat = bpy.data.materials[matname]
    ob.active_material = mat

def writeStokeToMesh(arr, jarr, MAINi, HORDERi, TIPSi, orig, gs, rpt=None):
    ###---MAIN BRANCH
    print('   WRITING MAIN BRANCH')
    llmain = []
    for x in MAINi:
        llmain.append(jarr[x])
    mob = writeArrayToMesh('la0MAIN', llmain, gs)
    mob.location = orig       

    ###---hORDER BRANCHES
    for hOi in range(len(HORDERi)):
        print('   WRITING ORDER', hOi)        
        hO = HORDERi[hOi]
        hob = newMesh('la1H'+str(hOi))

        for y in hO:
            llHO = []
            for x in y:
                llHO.append(jarr[x])
            addArrayToMesh(hob, llHO)
        hob.scale = (gs, gs, gs)
        hob.location = orig

    ###---TIPS
    print('   WRITING TIP PATHS')    
    tob = newMesh('la2TIPS')
    for y in  TIPSi:
        llt = []        
        for x in y:
            llt.append(jarr[x])
        addArrayToMesh(tob, llt)
    tob.scale = (gs, gs, gs)
    tob.location = orig

    ###---ADD MATERIALS TO OBJECTS (IF THEY EXIST)    
    try:
        addMaterial(mob, 'edgeMAT-h0')
        addMaterial(hob, 'edgeMAT-h1')
        addMaterial(tob, 'edgeMAT-h2')
        print('   ADDED MATERIALS')
    except: print('   MATERIALS NOT FOUND')
    ###---ADD GENERATION REPORT TO ALL MESHES
    if rpt:
        addReportProp(mob, rpt)
        addReportProp(hob, rpt)
        addReportProp(tob, rpt)                

def writeStokeToSingleMesh(arr, jarr, orig, gs, mct, rpt=None): 
    sgarr = buildCPGraph(arr, mct)
    llALL = []

    Aob = newMesh('laALL')
    for pt in jarr:
        addVert(Aob, pt)
    for cpi in range(len(sgarr)):
        ci = sgarr[cpi][0]
        pi = sgarr[cpi][1]
        addEdge(Aob, pi, ci)
    Aob.location = orig
    Aob.scale = ((gs,gs,gs))

    if rpt:
        addReportProp(Aob, rpt)

def visualizeArray(cg, oob, gs, vm, vs, vc, vv, rst):
###---IN: (cellgrid, origin, gridscale,
###   mulimesh, single mesh, cubes, voxels, report sting)
    origin = oob.location

    ###---DEAL WITH VERT MULTI-ORIGINS
    oct = 2
    if oob.type == 'MESH': oct = len(oob.data.vertices)

    ###---JITTER CELLS
    if vm or vs: cjarr = jitterCells(cg, 1)


    if vm:  ###---WRITE ARRAY TO MULTI MESH
        
        aMi, aHi, aTi = classifyStroke(cg, oct, winmgr.HORDER)
        print(':::WRITING TO MULTI-MESH')        
        writeStokeToMesh(cg, cjarr, aMi, aHi, aTi, origin, gs, rst)
        print(':::MULTI-MESH WRITTEN')

    if vs:  ###---WRITE TO SINGLE MESH
        print(':::WRITING TO SINGLE MESH')         
        writeStokeToSingleMesh(cg, cjarr, origin, gs, oct, rst)
        print(':::SINGLE MESH WRITTEN')
        
    if vc:  ###---WRITE ARRAY TO CUBE OBJECTS
        print(':::WRITING TO CUBES')
        writeArrayToCubes(cg, gs, origin)
        print(':::CUBES WRITTEN')

    if vv:  ###---WRITE ARRAY TO VOXEL DATA FILE
        print(':::WRITING TO VOXELS')
        fname = "FSLGvoxels.raw"
        path = os.path.dirname(bpy.data.filepath)
        writeArrayToVoxel(cg, path + "\\" + fname)
        print(':::VOXEL DATA WRITTEN TO - ', path + "\\" + fname)

    ###---READ/WRITE ARRAY TO FILE (MIGHT NOT BE NECESSARY)
    #tfile = 'c:\\testarr.txt'
    #writeArrayToFile(cg, tfile)
    #cg = readArrayFromFile(tfile)

    ###---READ/WRITE ARRAY TO CURVES (OUT OF ORDER)
    #writeArrayToCurves('laMAIN', llmain, .10, .25)        

######################################################################
########################### ALGORITHM FXNS ###########################
########################## FROM FALUAM PAPER #########################
###################### PLUS SOME STUFF I MADE UP #####################
######################################################################
def buildCPGraph(arr, sti = 2):
###---IN -XYZ ARRAY AS BUILT BY GENERATOR
###---OUT -[(CHILDindex, PARENTindex)]
###   sti - start index, 2 for Empty, len(me.vertices) for Mesh
    sgarr = []
    sgarr.append((1, 0)) #
    for ai in range(sti, len(arr)):
        cs = arr[ai]
        cpts = arr[0:ai]
        cslap = getStencil3D_26(cs[0], cs[1], cs[2])

        for nc in cslap:
            ct = cpts.count(nc)
            if ct>0:
                cti = cpts.index(nc)
        sgarr.append((ai, cti))
    return sgarr

def buildCPGraph_WORKINPROGRESS(arr, sti = 2):
###---IN -XYZ ARRAY AS BUILT BY GENERATOR
###---OUT -[(CHILDindex, PARENTindex)]
###   sti - start index, 2 for Empty, len(me.vertices) for Mesh
    sgarr = []
    sgarr.append((1, 0)) #
    ctix = 0
    for ai in range(sti, len(arr)):		
        cs = arr[ai]
        #cpts = arr[0:ai]
        cpts = arr[ctix:ai]
        cslap = getStencil3D_26(cs[0], cs[1], cs[2])
        for nc in cslap:
            ct = cpts.count(nc)
            if ct>0:
                #cti = cpts.index(nc)
                cti = ctix + cpts.index(nc)
                ctix = cpts.index(nc)
				
        sgarr.append((ai, cti))
    return sgarr

def findChargePath(oc, fc, ngraph, restrict = [], partial = True):
    ###---oc -ORIGIN CHARGE INDEX, fc -FINAL CHARGE INDEX
    ###---ngraph -NODE GRAPH, restrict- INDEX OF SITES CANNOT TRAVERSE
    ###---partial -RETURN PARTIAL PATH IF RESTRICTION ENCOUNTERD
    cList = splitList(ngraph, 0)
    pList = splitList(ngraph, 1)
    aRi = []
    cNODE = fc
    for x in range(len(ngraph)):
        pNODE = pList[cList.index(cNODE)]
        aRi.append(cNODE)
        cNODE = pNODE
        npNODECOUNT = cList.count(pNODE)
        if cNODE == oc:             ###   STOP IF ORIGIN FOUND
            aRi.append(cNODE)       ###   RETURN PATH
            return aRi
        if npNODECOUNT == 0:        ###   STOP IF NO PARENTS
            return []               ###   RETURN []
        if pNODE in restrict:       ###   STOP IF PARENT IS IN RESTRICTION
            if partial:             ###   RETURN PARTIAL OR []
                aRi.append(cNODE)
                return aRi
            else: return []

def findTips(arr):
    lt = []
    for ai in arr[0:len(arr)-1]:
        a = ai[0]
        cCOUNT = 0
        for bi in arr:
            b = bi[1]
            if a == b:
                cCOUNT += 1
        if cCOUNT == 0:
            lt.append(a)
    return lt

def findChannelRoots(path, ngraph, restrict = []):
    roots = []
    for ai in range(len(ngraph)):
        chi = ngraph[ai][0]
        par = ngraph[ai][1]
        if par in path and not chi in path and \
            not chi in restrict:        
            roots.append(par)
    droots = deDupe(roots)
    return droots

def findChannels(roots, tips, ngraph, restrict):
    cPATHS = []
    for ri in range(len(roots)):
        r = roots[ri]
        sL = 1
        sPATHi = []
        for ti in range(len(tips)):
            t = tips[ti]
            if t < r: continue
            tPATHi = findChargePath(r, t, ngraph, restrict, False)
            tL = len(tPATHi)
            if tL > sL:
                if countChildrenOnPath(tPATHi, ngraph) > 1:
                    sL = tL
                    sPATHi = tPATHi
                    tTEMP = t; tiTEMP = ti
        if len(sPATHi) > 0:
            print('   found path/idex from', ri, 'of', 
                  len(roots), 'possible | tips:', tTEMP, tiTEMP)
            cPATHS.append(sPATHi)
            tips.remove(tTEMP)
    return cPATHS

def findChannels_WORKINPROGRESS(roots, ttips, ngraph, restrict):
    cPATHS = []
    tips = list(ttips)
    for ri in range(len(roots)):
        r = roots[ri]
        sL = 1
        sPATHi = []
        tipREMOVE = [] ###---CHECKED TIP INDEXES, TO BE REMOVED FOR NEXT LOOP
        for ti in range(len(tips)):
            t = tips[ti]            
            #print('-CHECKING RT/IDEX:', r, ri, 'AGAINST TIP', t, ti)
            #if t < r: continue
            if ti < ri: continue
            tPATHi = findChargePath(r, t, ngraph, restrict, False)
            tL = len(tPATHi)
            if tL > sL:
                if countChildrenOnPath(tPATHi, ngraph) > 1:
                    sL = tL
                    sPATHi = tPATHi
                    tTEMP = t; tiTEMP = ti
            if tL > 0:
                tipREMOVE.append(t)                    
        if len(sPATHi) > 0:
            print('   found path from root idex', ri, 'of', 
                   len(roots), 'possible roots | #oftips=', len(tips))
            cPATHS.append(sPATHi)
        for q in tipREMOVE:  tips.remove(q)

    return cPATHS

def countChildrenOnPath(aPath, ngraph, quick = True):
    ###---RETURN HOW MANY BRANCHES 
    ###   COUNT WHEN NODE IS A PARENT >1 TIMES
    ###   quick -STOP AND RETURN AFTER FIRST
    cCOUNT = 0
    pList = splitList(ngraph,1)
    for ai in range(len(aPath)-1):
        ap = aPath[ai]
        pc = pList.count(ap)
        if quick and pc > 1: 
            return pc
    return cCOUNT

###---CLASSIFY CHANNELS INTO 'MAIN', 'hORDER/SECONDARY' and 'SIDE'
def classifyStroke(sarr, mct, hORDER = 1):
    print(':::CLASSIFYING STROKE')
    ###---BUILD CHILD/PARENT GRAPH (INDEXES OF sarr)  
    sgarr = buildCPGraph(sarr, mct)

    ###---FIND MAIN CHANNEL 
    print('   finding MAIN')
    oCharge = sgarr[0][1]
    fCharge = sgarr[len(sgarr)-1][0]
    aMAINi = findChargePath(oCharge, fCharge, sgarr)
    
    ###---FIND TIPS
    print('   finding TIPS')
    aTIPSi = findTips(sgarr)

    ###---FIND hORDER CHANNEL ROOTS
    ###   hCOUNT = ORDERS BEWTEEN MAIN and SIDE/TIPS
    ###   !!!STILL BUGGY!!!
    hRESTRICT = list(aMAINi)    ### ADD TO THIS AFTER EACH TIME
    allHPATHSi = []             ### ALL hO PATHS: [[h0], [h1]...]
    curPATHSi = [aMAINi]        ### LIST OF PATHS FIND ROOTS ON
    for h in range(hORDER):
        allHPATHSi.append([])
        for pi in range(len(curPATHSi)):     ###   LOOP THROUGH ALL PATHS IN THIS ORDER
            p = curPATHSi[pi]
            ###   GET ROOTS FOR THIS PATH
            aHROOTSi = findChannelRoots(p, sgarr, hRESTRICT)
            print('   found', len(aHROOTSi), 'roots in ORDER', h, ':#paths:', len(curPATHSi))
            ### GET CHANNELS FOR THESE ROOTS
            if len(aHROOTSi) == 0:
                print('NO ROOTS FOR FOUND FOR CHANNEL')
                aHPATHSi = []
                continue
            else:
                aHPATHSiD = findChannels(aHROOTSi, aTIPSi, sgarr, hRESTRICT)
                aHPATHSi = aHPATHSiD
                allHPATHSi[h] += aHPATHSi
                ###   SET THESE CHANNELS AS RESTRICTIONS FOR NEXT ITERATIONS
                for hri in aHPATHSi:
                    hRESTRICT += hri
        curPATHSi = aHPATHSi
    
    ###---SIDE BRANCHES, FINAL ORDER OF HEIRARCHY
    ###   FROM TIPS THAT ARE NOT IN AN EXISTING PATH
    ###   BACK TO ANY OTHER POINT THAT IS ALREADY ON A PATH
    aDRAWNi = []
    aDRAWNi += aMAINi
    for oH in allHPATHSi:
        for o in oH:
            aDRAWNi += o
    aTPATHSi = []
    for a in aTIPSi:
        if not a in aDRAWNi:
            aPATHi = findChargePath(oCharge, a, sgarr, aDRAWNi)
            aDRAWNi += aPATHi
            aTPATHSi.append(aPATHi)
            
    return aMAINi, allHPATHSi, aTPATHSi

def voxelByVertex(ob, gs):
###---'VOXELIZES' VERTS IN A MESH TO LIST [(x,y,z),(x,y,z)]
###   W/ RESPECT GSCALE AND OB ORIGIN (B/C SHOULD BE ORIGIN OBJ)
    orig = ob.location
    ll = []
    for v in ob.data.vertices:
        x = int( v.co.x / gs )
        y = int( v.co.y / gs )
        z = int( v.co.z / gs )      
        ll.append((x,y,z))
    return ll
    
def voxelByRays(ob, orig, gs):
###--- MESH INTO A 3DGRID W/ RESPECT GSCALE AND BOLT ORIGIN
###   -DOES NOT TAKE OBJECT ROTATION/SCALE INTO ACCOUNT
###   -THIS IS A HORRIBLE, INEFFICIENT FUNCTION
###    MAYBE THE RAYCAST/GRID THING ARE A BAD IDEA. BUT I 
###    HAVE TO 'VOXELIZE THE OBJECT W/ RESCT TO GSCALE/ORIGIN
    bbox = ob.bound_box
    bbxL = bbox[0][0]; bbxR = bbox[4][0]
    bbyL = bbox[0][1]; bbyR = bbox[2][1]
    bbzL = bbox[0][2]; bbzR = bbox[1][2]
    xct = int((bbxR - bbxL) / gs)
    yct = int((bbyR - bbyL) / gs)
    zct = int((bbzR - bbzL) / gs)
    xs = int(xct/2); ys = int(yct/2); zs = int(zct/2)
    print('  CASTING', xct, '/', yct, '/', zct, 'cells, total:', xct*yct*zct, 'in obj-', ob.name)    
    ll = []
    rc = 100    ###---DISTANCE TO CAST FROM
    ###---RAYCAST TOP/BOTTOM
    print('  RAYCASTING TOP/BOTTOM')
    for x in range(xct):
        for y in range(yct):
            xco = bbxL + (x*gs);  yco = bbyL + (y*gs)
            v1 = ((xco, yco,  rc));    v2 = ((xco, yco, -rc))            
            vz1 = ob.ray_cast(v1,v2);   vz2 = ob.ray_cast(v2,v1)            
            if vz1[2] != -1: ll.append((x-xs, y-ys, int(vz1[0][2] * (1/gs)) ))
            if vz2[2] != -1: ll.append((x-xs, y-ys, int(vz2[0][2] * (1/gs)) ))
    ###---RAYCAST FRONT/BACK
    print('  RAYCASTING FRONT/BACK')    
    for x in range(xct):
        for z in range(zct):
            xco = bbxL + (x*gs);  zco = bbzL + (z*gs)
            v1 = ((xco, rc,  zco));    v2 = ((xco, -rc, zco))            
            vy1 = ob.ray_cast(v1,v2);   vy2 = ob.ray_cast(v2,v1)            
            if vy1[2] != -1: ll.append((x-xs, int(vy1[0][1] * (1/gs)), z-zs))
            if vy2[2] != -1: ll.append((x-xs, int(vy2[0][1] * (1/gs)), z-zs))
    ###---RAYCAST LEFT/RIGHT
    print('  RAYCASTING LEFT/RIGHT')
    for y in range(yct):
        for z in range(zct):
            yco = bbyL + (y*gs);  zco = bbzL + (z*gs)
            v1 = ((rc, yco,  zco));    v2 = ((-rc, yco, zco))            
            vx1 = ob.ray_cast(v1,v2);   vx2 = ob.ray_cast(v2,v1)            
            if vx1[2] != -1: ll.append((int(vx1[0][0] * (1/gs)), y-ys, z-zs))            
            if vx2[2] != -1: ll.append((int(vx2[0][0] * (1/gs)), y-ys, z-zs))

    ###---ADD IN NEIGHBORS SO BOLT WONT GO THRU
    nlist = []
    for l in ll:
        nl = getStencil3D_26(l[0], l[1], l[2])
        nlist += nl

    ###---DEDUPE
    print('  ADDED NEIGHBORS, DEDUPING...')    
    rlist = deDupe(ll+nlist)
    qlist = []
    
    ###---RELOCATE GRID W/ RESPECT GSCALE AND BOLT ORIGIN
    ###   !!!NEED TO ADD IN OBJ ROT/SCALE HERE SOMEHOW...
    od = Vector(( (ob.location[0] - orig[0]) / gs,
                  (ob.location[1] - orig[1]) / gs,
                  (ob.location[2] - orig[2]) / gs ))
    for r in rlist:
        qlist.append((r[0]+int(od[0]), r[1]+int(od[1]), r[2]+int(od[2]) ))

    return qlist

def fakeGroundChargePlane(z, charge):
    eCL = []
    xy = abs(z)/2
    eCL += [(0, 0, z, charge)]    
    eCL += [(xy, 0, z, charge)]
    eCL += [(0, xy, z, charge)]
    eCL += [(-xy, 0, z, charge)]
    eCL += [(0, -xy, z, charge)]
    return eCL

def addCharges(ll, charge):
###---IN: ll - [(x,y,z), (x,y,z)], charge - w
###   OUT clist - [(x,y,z,w), (x,y,z,w)]
    clist = []
    for l in ll:
        clist.append((l[0], l[1], l[2], charge))
    return clist
        
######################################################################
########################### ALGORITHM FXNS ###########################
############################## FROM FSLG #############################
######################################################################
def getGrowthProbability_KEEPFORREFERENCE(uN, aList):
    ###---IN: uN -USER TERM, cList -CANDIDATE SITES, oList -CANDIDATE SITE CHARGES
    ###   OUT: LIST OF [(XYZ), POT, PROB]
    cList = splitList(aList, 0)
    oList = splitList(aList, 1)
    Omin, Omax = getLowHigh(oList)
    if Omin == Omax: Omax += notZero; Omin -= notZero
    PdL = []
    E = 0
    E = notZero   ###===DIVISOR FOR (FSLG - Eqn. 12)
    for o in oList:
        Uj = (o - Omin) / (Omax - Omin) ###===(FSLG - Eqn. 13)
        E += pow(Uj, uN)
    for oi in range(len(oList)):
        o = oList[oi]
        Ui = (o - Omin) / (Omax - Omin)
        Pd = (pow(Ui, uN)) / E ###===(FSLG - Eqn. 12)
        PdINT = Pd * 100
        PdL.append(Pd)
    return PdL 

###---WORK IN PROGRESS, TRYING TO SPEED THESE UP
def fslg_e13(x, min, max, u): return pow((x - min) / (max - min), u)
def addit(x,y):return x+y
def fslg_e12(x, min, max, u, e): return (fslg_e13(x, min, max, u) / e) * 100

def getGrowthProbability(uN, aList):
    ###---IN: uN -USER TERM, cList -CANDIDATE SITES, oList -CANDIDATE SITE CHARGES
    ###   OUT: LIST OF PROB
    cList = splitList(aList, 0)
    oList = splitList(aList, 1)
    Omin, Omax = getLowHigh(oList)
    if Omin == Omax: Omax += notZero; Omin -= notZero
    PdL = []
    E = notZero
    minL = [Omin for q in range(len(oList))]
    maxL = [Omax for q in range(len(oList))]
    uNL =  [uN   for q in range(len(oList))]
    E = sum(map(fslg_e13, oList, minL, maxL, uNL))
    EL = [E for q in range(len(oList))]
    mp = map(fslg_e12, oList, minL, maxL, uNL, EL)
    for m in mp: PdL.append(m)
    return PdL 

def updatePointCharges(p, cList, eList = []):
    ###---IN: pNew -NEW GROWTH CELL
    ###       cList -OLD CANDIDATE SITES, eList -SAME
    ###   OUT: LIST OF NEW CHARGE AT CANDIDATE SITES
    r1 = 1/2        ###===(FSLG - Eqn. 10)
    nOiL = []    
    for oi in range(len(cList)):
        o = cList[oi][1]
        c = cList[oi][0]
        iOe = 0
        rit = dist(c[0], c[1], c[2], p[0], p[1], p[2])        
        iOe += (1 - (r1/rit))
        Oit =  o + iOe            
        nOiL.append((c, Oit))
    return nOiL

def initialPointCharges(pList, cList, eList = []):
    ###---IN: p -CHARGED CELL (XYZ), cList -CANDIDATE SITES (XYZ, POT, PROB)
    ###   OUT: cList -WITH POTENTIAL CALCULATED 
    r1 = 1/2        ###===(FSLG - Eqn. 10)
    npList = []
    for p in pList:
        npList.append(((p[0], p[1], p[2]), 1.0))
    for e in eList:
        npList.append(((e[0], e[1], e[2]), e[3]))
    OiL = []
    for i in cList:
        Oi = 0
        for j in npList:
            if i != j[0]:
                rij = dist(i[0], i[1], i[2], j[0][0], j[0][1], j[0][2])
                Oi += (1 - (r1 / rij)) * j[1] ### CHARGE INFLUENCE
        OiL.append(((i[0], i[1], i[2]), Oi))
    return OiL

def getCandidateSites(aList, iList = []):
    ###---IN: aList -(X,Y,Z) OF CHARGED CELL SITES, iList -insulator sites
    ###   OUT: CANDIDATE LIST OF GROWTH SITES [(X,Y,Z)]
    tt1 = time.clock()    
    cList = []
    for c in aList:
        tempList = getStencil3D_26(c[0], c[1], c[2])
        for t in tempList:
            if not t in aList and not t in iList:
                cList.append(t)
    ncList = deDupe(cList)
    tt2 = time.clock()	
    #print('FXNTIMER:getCandidateSites:', tt2-tt1, 'check 26 against:', len(aList)+len(iList))    
    return ncList

######################################################################
############################# SETUP FXNS #############################
######################################################################
def setupObjects():
    #if winmgr.OOB == "" or winmgr.OOB.name not in scene...
    oOB = bpy.data.objects.new('ELorigin', None)
    oOB.location = ((0,0,10))
    bpy.context.scene.objects.link(oOB)

    gOB = bpy.data.objects.new('ELground', None)
    gOB.empty_draw_type = 'ARROWS'
    bpy.context.scene.objects.link(gOB)
    
    cME = makeMeshCube(1)
    cOB = bpy.data.objects.new('ELcloud', cME)
    cOB.location = ((-2,8,12))
    cOB.hide_render = True    
    bpy.context.scene.objects.link(cOB)
    
    iME = makeMeshCube(1)
    for v in iME.vertices: 
        xyl = 6.5; zl = .5
        v.co[0] = v.co[0] * xyl
        v.co[1] = v.co[1] * xyl
        v.co[2] = v.co[2] * zl
    iOB = bpy.data.objects.new('ELinsulator', iME)    
    iOB.location = ((0,0,5))
    iOB.hide_render = True
    bpy.context.scene.objects.link(iOB)

    try:
        winmgr.OOB = 'ELorigin'
        winmgr.GOB = 'ELground'
        winmgr.COB = 'ELcloud'
        winmgr.IOB = 'ELinsulator'
    except: pass

def checkSettings():
    check = True
    if winmgr.OOB == "": 
        print('ERROR: NO ORIGIN OBJECT SELECTED')
        check = False
    if winmgr.GROUNDBOOL and winmgr.GOB == "":
        print('ERROR: NO GROUND OBJECT SELECTED')
        check = False
    if winmgr.CLOUDBOOL and winmgr.COB == "":
        print('ERROR: NO CLOUD OBJECT SELECTED')        
        check = False
    if winmgr.IBOOL and winmgr.IOB == "":
        print('ERROR: NO INSULATOR OBJECT SELECTED')        
        check = False
    #should make a popup here
    return check


######################################################################
############################### MAIN #################################
######################################################################
def FSLG():
###======FAST SIMULATION OF LAPLACIAN GROWTH======###
    print('\n<<<<<<------GO GO GADGET: FAST SIMULATION OF LAPLACIAN GROWTH!')
    tc1 = time.clock()
    TSTEPS = winmgr.TSTEPS

    #obORIGIN = scn.objects[winmgr.OOB]    
    #obGROUND = scn.objects[winmgr.GOB]
    obORIGIN = bpy.context.scene.objects[winmgr.OOB]
    obGROUND = bpy.context.scene.objects[winmgr.GOB]        
    winmgr.ORIGIN = obORIGIN.location
    winmgr.GROUNDZ = int((obGROUND.location[2] - winmgr.ORIGIN[2]) / winmgr.GSCALE)
    
    ###====== 1) INSERT INTIAL CHARGE(S) POINT (USES VERTS IF MESH)
    cgrid = [(0, 0, 0)]
    if obORIGIN.type == 'MESH':
        print("<<<<<<------ORIGIN OBJECT IS MESH, 'VOXELIZING' INTIAL CHARGES FROM VERTS")
        cgrid = voxelByVertex(obORIGIN, winmgr.GSCALE)
        if winmgr.VMMESH:
            print("<<<<<<------CANNOT CLASSIFY STROKE FROM VERT ORIGINS YET, NO MULTI-MESH OUTPUT")
            winmgr.VMMESH = False; winmgr.VSMESH = True

    ###---GROUND CHARGE CELL / INSULATOR LISTS (eChargeList/icList)
    eChargeList = []; icList = []
    if winmgr.GROUNDBOOL:
        eChargeList = fakeGroundChargePlane(winmgr.GROUNDZ, winmgr.GROUNDC)
    if winmgr.CLOUDBOOL:
        print("<<<<<<------'VOXELIZING' CLOUD OBJECT (COULD TAKE SOME TIME)")
        obCLOUD = bpy.context.scene.objects[winmgr.COB]
        eChargeListQ = voxelByRays(obCLOUD, winmgr.ORIGIN, winmgr.GSCALE)
        eChargeList = addCharges(eChargeListQ, winmgr.CLOUDC)
        print('<<<<<<------CLOUD OBJECT CELL COUNT = ', len(eChargeList) )        
    if winmgr.IBOOL:
        print("<<<<<<------'VOXELIZING' INSULATOR OBJECT (COULD TAKE SOME TIME)")
        obINSULATOR = bpy.context.scene.objects[winmgr.IOB]
        icList = voxelByRays(obINSULATOR, winmgr.ORIGIN, winmgr.GSCALE)
        print('<<<<<<------INSULATOR OBJECT CELL COUNT = ', len(icList) )
        #writeArrayToCubes(icList, winmgr.GSCALE, winmgr.ORIGIN)
        #return 'THEEND'
        
    ###====== 2) LOCATE CANDIDATE SITES AROUND CHARGE
    cSites = getCandidateSites(cgrid, icList)
    
    ###====== 3) CALC POTENTIAL AT EACH SITE (Eqn. 10)
    cSites = initialPointCharges(cgrid, cSites, eChargeList)
    
    ts = 1
    while ts <= TSTEPS:
        ###====== 1) SELECT NEW GROWTH SITE (Eqn. 12)
        ###===GET PROBABILITIES AT CANDIDATE SITES
        gProbs = getGrowthProbability(winmgr.BIGVAR, cSites)
        ###===CHOOSE NEW GROWTH SITE BASED ON PROBABILITIES
        gSitei = weightedRandomChoice(gProbs)
        gsite  = cSites[gSitei][0]

        ###====== 2) ADD NEW POINT CHARGE AT GROWTH SITE
        ###===ADD NEW GROWTH CELL TO GRID
        cgrid.append(gsite)
        ###===REMOVE NEW GROWTH CELL FROM CANDIDATE SITES
        cSites.remove(cSites[gSitei])

        ###====== 3) UPDATE POTENTIAL AT CANDIDATE SITES (Eqn. 11)
        cSites = updatePointCharges(gsite, cSites, eChargeList)        

        ###====== 4) ADD NEW CANDIDATES SURROUNDING GROWTH SITE
        ###===GET CANDIDATE 'STENCIL'
        ncSitesT = getCandidateSites([gsite], icList)
        ###===REMOVE CANDIDATES ALREADY IN CANDIDATE LIST OR CHARGE GRID
        ncSites = []
        cSplit = splitList(cSites, 0)
        for cn in ncSitesT:
            if not cn in cSplit and \
            not cn in cgrid:
                ncSites.append((cn, 0))

        ###====== 5) CALC POTENTIAL AT NEW CANDIDATE SITES (Eqn. 10)
        ncSplit = splitList(ncSites, 0)        
        ncSites = initialPointCharges(cgrid, ncSplit, eChargeList)

        ###===ADD NEW CANDIDATE SITES TO CANDIDATE LIST
        for ncs in ncSites:
            cSites.append(ncs)

        ###===ITERATION COMPLETE
        istr1 = ':::T-STEP: ' + str(ts) + '/' + str(TSTEPS) 
        istr12 = ' | GROUNDZ: ' + str(winmgr.GROUNDZ) + ' | '
        istr2 = 'CANDS: ' + str(len(cSites)) + ' | '
        istr3 = 'GSITE: ' + str(gsite)
        print(istr1 + istr12 + istr2 + istr3)        
        ts += 1
        
        ###---EARLY TERMINATION FOR GROUND/CLOUD STRIKE
        if winmgr.GROUNDBOOL:
            if gsite[2] == winmgr.GROUNDZ:
                ts = TSTEPS+1
                print('<<<<<<------EARLY TERMINATION DUE TO GROUNDSTRIKE')
                continue
        if winmgr.CLOUDBOOL:
            #if gsite in cloudList:
            if gsite in splitListCo(eChargeList):
                ts = TSTEPS+1
                print('<<<<<<------EARLY TERMINATION DUE TO CLOUDSTRIKE')
                continue            

    tc2 = time.clock()
    tcRUN = tc2 - tc1
    print('<<<<<<------LAPLACIAN GROWTH LOOP COMPLETED: ' + str(len(cgrid)) + ' / ' + str(tcRUN)[0:5] + ' SECONDS')
    print('<<<<<<------VISUALIZING DATA')

    reportSTRING = getReportString(tcRUN)    
    ###---VISUALIZE ARRAY
    visualizeArray(cgrid, obORIGIN, winmgr.GSCALE, winmgr.VMMESH, winmgr.VSMESH, winmgr.VCUBE, winmgr.VVOX, reportSTRING)
    print('<<<<<<------COMPLETE')

######################################################################
################################ GUI #################################
######################################################################
###---NOT IN UI
bpy.types.WindowManager.ORIGIN = bpy.props.FloatVectorProperty(name = "origin charge")
bpy.types.WindowManager.GROUNDZ = bpy.props.IntProperty(name = "ground Z coordinate")
bpy.types.WindowManager.HORDER = bpy.props.IntProperty(name = "secondary paths orders")
###---IN UI
bpy.types.WindowManager.TSTEPS = bpy.props.IntProperty(
    name = "iterations", description = "number of cells to create, will end early if hits ground plane or cloud")
bpy.types.WindowManager.GSCALE = bpy.props.FloatProperty(
    name = "grid unit size", description = "scale of cells, .25 = 4 cells per blenderUnit")
bpy.types.WindowManager.BIGVAR = bpy.props.FloatProperty(
    name = "straightness", description = "straightness/branchiness of bolt, <2 is mush, >12 is staight line, 6.3 is good")
bpy.types.WindowManager.GROUNDBOOL = bpy.props.BoolProperty(
    name = "use ground object", description = "use ground plane or not")
bpy.types.WindowManager.GROUNDC = bpy.props.IntProperty(
    name = "ground charge", description = "charge of ground plane")
bpy.types.WindowManager.CLOUDBOOL = bpy.props.BoolProperty(
    name = "use cloud object", description = "use cloud obj, attracts and terminates like ground but any obj instead of z plane, can slow down loop if obj is large, overrides ground")
bpy.types.WindowManager.CLOUDC = bpy.props.IntProperty(
    name = "cloud charge", description = "charge of a cell in cloud object (so total charge also depends on obj size)")

bpy.types.WindowManager.VMMESH = bpy.props.BoolProperty(
    name = "multi mesh", description = "output to multi-meshes for different materials on main/sec/side branches")
bpy.types.WindowManager.VSMESH = bpy.props.BoolProperty(
    name = "single mesh", description = "output to single mesh for using build modifier and particles for effects")
bpy.types.WindowManager.VCUBE = bpy.props.BoolProperty(
    name = "cubes", description = "CTRL-J after run to JOIN, outputs a bunch of cube objest, mostly for testing")
bpy.types.WindowManager.VVOX = bpy.props.BoolProperty(        
    name = "voxel (experimental)", description = "output to a voxel file to bpy.data.filepath\FSLGvoxels.raw - doesn't work well right now")
bpy.types.WindowManager.IBOOL = bpy.props.BoolProperty(
    name = "use insulator object", description = "use insulator mesh object to prevent growth of bolt in areas")
bpy.types.WindowManager.OOB = bpy.props.StringProperty(description = "origin of bolt, can be an Empty, if obj is mesh will use all verts as charges")
bpy.types.WindowManager.GOB = bpy.props.StringProperty(description = "object to use as ground plane, uses z coord only")
bpy.types.WindowManager.COB = bpy.props.StringProperty(description = "object to use as cloud, best to use a cube")
bpy.types.WindowManager.IOB = bpy.props.StringProperty(description = "object to use as insulator, 'voxelized' before generating bolt, can be slow")

###---DEFAULT USER SETTINGS
winmgr.TSTEPS = 350
winmgr.HORDER = 1
winmgr.GSCALE = 0.12
winmgr.BIGVAR = 6.3
winmgr.GROUNDBOOL = True
winmgr.GROUNDC = -250
winmgr.CLOUDBOOL = False
winmgr.CLOUDC = -1
winmgr.VMMESH = True
winmgr.VSMESH = False
winmgr.VCUBE = False
winmgr.VVOX = False
winmgr.IBOOL = False
try:
    winmgr.OOB = "ELorigin"
    winmgr.GOB = "ELground"
    winmgr.COB = "ELcloud"
    winmgr.IOB = "ELinsulator"    
except: pass

###---TESTING USER SETTINGS
if False:
#if True:
    winmgr.TSTEPS = 40
    #winmgr.HORDER = 1
    #winmgr.GSCALE = 0.12    
    #winmgr.BIGVAR = 6.3
    winmgr.GROUNDBOOL = True
    #winmgr.GROUNDC = -500
    winmgr.CLOUDBOOL = True
    #winmgr.CLOUDC = -5
    #winmgr.VMMESH = True
    #winmgr.VSMESH = True
    #winmgr.VCUBE = True
    #winmgr.VVOX = True
    winmgr.IBOOL = True

class runFSLGLoopOperator(bpy.types.Operator):
    '''By The Mighty Hammer Of Thor!!!'''
    bl_idname = "object.runfslg_operator"
    bl_label = "run FSLG Loop Operator"

    def execute(self, context):
        if checkSettings():
            FSLG()
        else: pass
        return {'FINISHED'}
    
class setupObjectsOperator(bpy.types.Operator):
    '''create origin/ground/cloud/insulator objects'''
    bl_idname = "object.setup_objects_operator"
    bl_label = "Setup Objects Operator"

    def execute(self, context):
        setupObjects()        
        return {'FINISHED'}    

class OBJECT_PT_fslg(bpy.types.Panel):
    bl_label = "Laplacian Lightning - v0.2.6"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Create"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        colR = layout.column()        
        #row1 = layout.row()
        #colL = row1.column()
        #colR = row1.column()
        colR.label('-for progress open console-')
        colR.label('Help > Toggle System Console')        
        colR.prop(winmgr, 'TSTEPS')
        colR.prop(winmgr, 'GSCALE')        
        colR.prop(winmgr, 'BIGVAR')
        colR.operator('object.setup_objects_operator', text = 'create setup objects')        
        colR.label('origin object')
        colR.prop_search(winmgr, "OOB",  context.scene, "objects")        
        colR.prop(winmgr, 'GROUNDBOOL')
        colR.prop_search(winmgr, "GOB",  context.scene, "objects")        
        colR.prop(winmgr, 'GROUNDC') 
        colR.prop(winmgr, 'CLOUDBOOL')
        colR.prop_search(winmgr, "COB",  context.scene, "objects")        
        colR.prop(winmgr, 'CLOUDC')
        colR.prop(winmgr, 'IBOOL')
        colR.prop_search(winmgr, "IOB",  context.scene, "objects")
        colR.operator('object.runfslg_operator', text = 'generate lightning')
        #col.prop(winmgr, 'HORDER')
        colR.prop(winmgr, 'VMMESH')
        colR.prop(winmgr, 'VSMESH')        
        colR.prop(winmgr, 'VCUBE')
        #colR.prop(winmgr, 'VVOX')

def getReportString(rtime):
    rSTRING1 = 't:' + str(winmgr.TSTEPS) + ',sc:' + str(winmgr.GSCALE)[0:4] + ',uv:' + str(winmgr.BIGVAR)[0:4] + ',' 
    rSTRING2 = 'ori:' + str(winmgr. ORIGIN[0]) + '/' + str(winmgr. ORIGIN[1]) + '/' + str(winmgr. ORIGIN[2]) + ','
    rSTRING3 = 'gz:' + str(winmgr.GROUNDZ) + ',gc:' + str(winmgr.GROUNDC) + ',rtime:' + str(int(rtime))
    return rSTRING1 + rSTRING2 + rSTRING3

def addReportProp(ob, str):
    bpy.types.Object.FSLG_REPORT = bpy.props.StringProperty(
	   name = 'fslg_report', default = '')
    ob.FSLG_REPORT = str
        
def register():
    bpy.utils.register_class(runFSLGLoopOperator)    
    bpy.utils.register_class(setupObjectsOperator)
    bpy.utils.register_class(OBJECT_PT_fslg)

def unregister():
    bpy.utils.unregister_class(runFSLGLoopOperator)    
    bpy.utils.unregister_class(setupObjectsOperator)    
    bpy.utils.unregister_class(OBJECT_PT_fslg)

if __name__ == "__main__":
    ### RUN FOR TESTING
    #FSLG()
    
    ### UI
    register()
    pass

###########################
##### FXN BENCHMARKS ######
###########################
def BENCH():
    print('\n\n\n--->BEGIN BENCHMARK')
    bt0 = time.clock()
    ###---MAKE A BIG LIST
    tsize = 25
    tlist = []
    for x in range(tsize):
        for y in range(tsize):
            for z in range(tsize):
                tlist.append((x,y,z))
                tlist.append((x,y,z))

    ###---FUNCTION TO TEST
    bt1 = time.clock()

    #ll = deDupe(tlist)
    #ll = f5(tlist)
    print('LENS - ', len(tlist), len(ll) )

    bt2 = time.clock()
    btRUNb = bt2 - bt1
    btRUNa = bt1 - bt0
    print('--->SETUP TIME    : ', btRUNa)
    print('--->BENCHMARK TIME: ', btRUNb)
    print('--->GRIDSIZE: ', tsize, ' - ', tsize*tsize*tsize)
    
#BENCH()

######################################################################
############################### THE END ##############################
######################################################################
