# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

bl_info = {
    "name": "IvyGen",
    "author": "testscreenings, PKHG, TrumanBlending",
    "version": (0, 1, 5),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Ivy Generator (Create Tab)",
    "description": "Adds generated ivy to a mesh object starting "
                   "at the 3D cursor",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/ivy_gen.html",
    "category": "Add Curve",
}


import bpy
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
)
from mathutils.bvhtree import BVHTree
from mathutils import (
    Vector,
    Matrix,
)
from collections import deque
from math import (
    pow, cos,
    pi, atan2,
)
from random import (
    random as rand_val,
    seed as rand_seed,
)
import time


def createIvyGeometry(IVY, growLeaves):
    """Create the curve geometry for IVY"""
    # Compute the local size and the gauss weight filter
    # local_ivyBranchSize = IVY.ivyBranchSize  # * radius * IVY.ivySize
    gaussWeight = (1.0, 2.0, 4.0, 7.0, 9.0, 10.0, 9.0, 7.0, 4.0, 2.0, 1.0)

    # Create a new curve and initialise it
    curve = bpy.data.curves.new("IVY", type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 1
    curve.fill_mode = 'FULL'
    curve.resolution_u = 4

    if growLeaves:
        # Create the ivy leaves
        # Order location of the vertices
        signList = ((-1.0, +1.0),
                    (+1.0, +1.0),
                    (+1.0, -1.0),
                    (-1.0, -1.0),
                    )

        # Get the local size
        # local_ivyLeafSize = IVY.ivyLeafSize  # * radius * IVY.ivySize

        # Initialise the vertex and face lists
        vertList = deque()

        # Store the methods for faster calling
        addV = vertList.extend
        rotMat = Matrix.Rotation

    # Loop over all roots to generate its nodes
    for root in IVY.ivyRoots:
        # Only grow if more than one node
        numNodes = len(root.ivyNodes)
        if numNodes > 1:
            # Calculate the local radius
            local_ivyBranchRadius = 1.0 / (root.parents + 1) + 1.0
            prevIvyLength = 1.0 / root.ivyNodes[-1].length
            splineVerts = [ax for n in root.ivyNodes for ax in n.pos.to_4d()]

            radiusConstant = local_ivyBranchRadius * IVY.ivyBranchSize
            splineRadii = [radiusConstant * (1.3 - n.length * prevIvyLength)
                           for n in root.ivyNodes]

            # Add the poly curve and set coords and radii
            newSpline = curve.splines.new(type='POLY')
            newSpline.points.add(len(splineVerts) // 4 - 1)
            newSpline.points.foreach_set('co', splineVerts)
            newSpline.points.foreach_set('radius', splineRadii)

            # Loop over all nodes in the root
            for i, n in enumerate(root.ivyNodes):
                for k in range(len(gaussWeight)):
                    idx = max(0, min(i + k - 5, numNodes - 1))
                    n.smoothAdhesionVector += (gaussWeight[k] *
                                               root.ivyNodes[idx].adhesionVector)
                n.smoothAdhesionVector /= 56.0
                n.adhesionLength = n.smoothAdhesionVector.length
                n.smoothAdhesionVector.normalize()

                if growLeaves and (i < numNodes - 1):
                    node = root.ivyNodes[i]
                    nodeNext = root.ivyNodes[i + 1]

                    # Find the weight and normalize the smooth adhesion vector
                    weight = pow(node.length * prevIvyLength, 0.7)

                    # Calculate the ground ivy and the new weight
                    groundIvy = max(0.0, -node.smoothAdhesionVector.z)
                    weight += groundIvy * pow(1 - node.length *
                                                              prevIvyLength, 2)

                    # Find the alignment weight
                    alignmentWeight = node.adhesionLength

                    # Calculate the needed angles
                    phi = atan2(node.smoothAdhesionVector.y,
                                node.smoothAdhesionVector.x) - pi / 2.0

                    theta = (0.5 *
                        node.smoothAdhesionVector.angle(Vector((0, 0, -1)), 0))

                    # Find the size weight
                    sizeWeight = 1.5 - (cos(2 * pi * weight) * 0.5 + 0.5)

                    # Randomise the angles
                    phi += (rand_val() - 0.5) * (1.3 - alignmentWeight)
                    theta += (rand_val() - 0.5) * (1.1 - alignmentWeight)

                    # Calculate the leaf size an append the face to the list
                    leafSize = IVY.ivyLeafSize * sizeWeight

                    for j in range(10):
                        # Generate the probability
                        probability = rand_val()

                        # If we need to grow a leaf, do so
                        if (probability * weight) > IVY.leafProbability:

                            # Generate the random vector
                            randomVector = Vector((rand_val() - 0.5,
                                                   rand_val() - 0.5,
                                                   rand_val() - 0.5,
                                                   ))

                            # Find the leaf center
                            center = (node.pos.lerp(nodeNext.pos, j / 10.0) +
                                               IVY.ivyLeafSize * randomVector)

                            # For each of the verts, rotate/scale and append
                            basisVecX = Vector((1, 0, 0))
                            basisVecY = Vector((0, 1, 0))

                            horiRot = rotMat(theta, 3, 'X')
                            vertRot = rotMat(phi, 3, 'Z')

                            basisVecX.rotate(horiRot)
                            basisVecY.rotate(horiRot)

                            basisVecX.rotate(vertRot)
                            basisVecY.rotate(vertRot)

                            basisVecX *= leafSize
                            basisVecY *= leafSize

                            addV([k1 * basisVecX + k2 * basisVecY + center for
                                                           k1, k2 in signList])

    # Add the object and link to scene
    newCurve = bpy.data.objects.new("IVY_Curve", curve)
    bpy.context.collection.objects.link(newCurve)

    if growLeaves:
        faceList = [[4 * i + l for l in range(4)] for i in
                    range(len(vertList) // 4)]

        # Generate the new leaf mesh and link
        me = bpy.data.meshes.new('IvyLeaf')
        me.from_pydata(vertList, [], faceList)
        me.update(calc_edges=True)
        ob = bpy.data.objects.new('IvyLeaf', me)
        bpy.context.collection.objects.link(ob)

        me.uv_layers.new(name="Leaves")

        # Set the uv texture coords
        # TODO, this is non-functional, default uvs are ok?
        '''
        for d in tex.data:
            uv1, uv2, uv3, uv4 = signList
        '''

        ob.parent = newCurve


class IvyNode:
    """ The basic class used for each point on the ivy which is grown."""
    __slots__ = ('pos', 'primaryDir', 'adhesionVector', 'adhesionLength',
                 'smoothAdhesionVector', 'length', 'floatingLength', 'climb')

    def __init__(self):
        self.pos = Vector((0, 0, 0))
        self.primaryDir = Vector((0, 0, 1))
        self.adhesionVector = Vector((0, 0, 0))
        self.smoothAdhesionVector = Vector((0, 0, 0))
        self.length = 0.0001
        self.floatingLength = 0.0
        self.climb = True


class IvyRoot:
    """ The class used to hold all ivy nodes growing from this root point."""
    __slots__ = ('ivyNodes', 'alive', 'parents')

    def __init__(self):
        self.ivyNodes = deque()
        self.alive = True
        self.parents = 0


class Ivy:
    """ The class holding all parameters and ivy roots."""
    __slots__ = ('ivyRoots', 'primaryWeight', 'randomWeight',
                 'gravityWeight', 'adhesionWeight', 'branchingProbability',
                 'leafProbability', 'ivySize', 'ivyLeafSize', 'ivyBranchSize',
                 'maxFloatLength', 'maxAdhesionDistance', 'maxLength')

    def __init__(self,
                 primaryWeight=0.5,
                 randomWeight=0.2,
                 gravityWeight=1.0,
                 adhesionWeight=0.1,
                 branchingProbability=0.05,
                 leafProbability=0.35,
                 ivySize=0.02,
                 ivyLeafSize=0.02,
                 ivyBranchSize=0.001,
                 maxFloatLength=0.5,
                 maxAdhesionDistance=1.0):

        self.ivyRoots = deque()
        self.primaryWeight = primaryWeight
        self.randomWeight = randomWeight
        self.gravityWeight = gravityWeight
        self.adhesionWeight = adhesionWeight
        self.branchingProbability = 1 - branchingProbability
        self.leafProbability = 1 - leafProbability
        self.ivySize = ivySize
        self.ivyLeafSize = ivyLeafSize
        self.ivyBranchSize = ivyBranchSize
        self.maxFloatLength = maxFloatLength
        self.maxAdhesionDistance = maxAdhesionDistance
        self.maxLength = 0.0

        # Normalize all the weights only on initialisation
        sums = self.primaryWeight + self.randomWeight + self.adhesionWeight
        self.primaryWeight /= sums
        self.randomWeight /= sums
        self.adhesionWeight /= sums

    def seed(self, seedPos):
        # Seed the Ivy by making a new root and first node
        tmpRoot = IvyRoot()
        tmpIvy = IvyNode()
        tmpIvy.pos = seedPos

        tmpRoot.ivyNodes.append(tmpIvy)
        self.ivyRoots.append(tmpRoot)

    def grow(self, ob, bvhtree):
        # Determine the local sizes
        # local_ivySize = self.ivySize  # * radius
        # local_maxFloatLength = self.maxFloatLength  # * radius
        # local_maxAdhesionDistance = self.maxAdhesionDistance  # * radius

        for root in self.ivyRoots:
            # Make sure the root is alive, if not, skip
            if not root.alive:
                continue

            # Get the last node in the current root
            prevIvy = root.ivyNodes[-1]

            # If the node is floating for too long, kill the root
            if prevIvy.floatingLength > self.maxFloatLength:
                root.alive = False

            # Set the primary direction from the last node
            primaryVector = prevIvy.primaryDir

            # Make the random vector and normalize
            randomVector = Vector((rand_val() - 0.5, rand_val() - 0.5,
                                   rand_val() - 0.5)) + Vector((0, 0, 0.2))
            randomVector.normalize()

            # Calculate the adhesion vector
            adhesionVector = adhesion(
                    prevIvy.pos, bvhtree, self.maxAdhesionDistance)

            # Calculate the growing vector
            growVector = self.ivySize * (primaryVector * self.primaryWeight +
                                          randomVector * self.randomWeight +
                                          adhesionVector * self.adhesionWeight)

            # Find the gravity vector
            gravityVector = (self.ivySize * self.gravityWeight *
                                                            Vector((0, 0, -1)))
            gravityVector *= pow(prevIvy.floatingLength / self.maxFloatLength,
                                 0.7)

            # Determine the new position vector
            newPos = prevIvy.pos + growVector + gravityVector

            # Check for collisions with the object
            climbing, newPos = collision(bvhtree, prevIvy.pos, newPos)

            # Update the growing vector for any collisions
            growVector = newPos - prevIvy.pos - gravityVector
            growVector.normalize()

            # Create a new IvyNode and set its properties
            tmpNode = IvyNode()
            tmpNode.climb = climbing
            tmpNode.pos = newPos
            tmpNode.primaryDir = prevIvy.primaryDir.lerp(growVector, 0.5)
            tmpNode.primaryDir.normalize()
            tmpNode.adhesionVector = adhesionVector
            tmpNode.length = prevIvy.length + (newPos - prevIvy.pos).length

            if tmpNode.length > self.maxLength:
                self.maxLength = tmpNode.length

            # If the node isn't climbing, update it's floating length
            # Otherwise set it to 0
            if not climbing:
                tmpNode.floatingLength = prevIvy.floatingLength + (newPos -
                                                            prevIvy.pos).length
            else:
                tmpNode.floatingLength = 0.0

            root.ivyNodes.append(tmpNode)

        # Loop through all roots to check if a new root is generated
        for root in self.ivyRoots:
            # Check the root is alive and isn't at high level of recursion
            if (root.parents > 3) or (not root.alive):
                continue

            # Check to make sure there's more than 1 node
            if len(root.ivyNodes) > 1:
                # Loop through all nodes in root to check if new root is grown
                for node in root.ivyNodes:
                    # Set the last node of the root and find the weighting
                    prevIvy = root.ivyNodes[-1]
                    weight = 1.0 - (cos(2.0 * pi * node.length /
                                        prevIvy.length) * 0.5 + 0.5)

                    probability = rand_val()

                    # Check if a new root is grown and if so, set its values
                    if (probability * weight > self.branchingProbability):
                        tmpNode = IvyNode()
                        tmpNode.pos = node.pos
                        tmpNode.floatingLength = node.floatingLength

                        tmpRoot = IvyRoot()
                        tmpRoot.parents = root.parents + 1

                        tmpRoot.ivyNodes.append(tmpNode)
                        self.ivyRoots.append(tmpRoot)
                        return


def adhesion(loc, bvhtree, max_l):
    # Compute the adhesion vector by finding the nearest point
    nearest_location, *_ = bvhtree.find_nearest(loc, max_l)
    adhesion_vector = Vector((0.0, 0.0, 0.0))
    if nearest_location is not None:
        # Compute the distance to the nearest point
        adhesion_vector = nearest_location - loc
        distance = adhesion_vector.length
        # If it's less than the maximum allowed and not 0, continue
        if distance:
            # Compute the direction vector between the closest point and loc
            adhesion_vector.normalize()
            adhesion_vector *= 1.0 - distance / max_l
            # adhesion_vector *= getFaceWeight(ob.data, nearest_result[3])
    return adhesion_vector


def collision(bvhtree, pos, new_pos):
    # Check for collision with the object
    climbing = False

    corrected_new_pos = new_pos
    direction = new_pos - pos

    hit_location, hit_normal, *_ = bvhtree.ray_cast(pos, direction, direction.length)
    # If there's a collision we need to check it
    if hit_location is not None:
        # Check whether the collision is going into the object
        if direction.dot(hit_normal) < 0.0:
            reflected_direction = (new_pos - hit_location).reflect(hit_normal)

            corrected_new_pos = hit_location + reflected_direction
            climbing = True

    return climbing, corrected_new_pos


def bvhtree_from_object(ob):
    import bmesh
    bm = bmesh.new()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    ob_eval = ob.evaluated_get(depsgraph)
    mesh = ob_eval.to_mesh()
    bm.from_mesh(mesh)
    bm.transform(ob.matrix_world)

    bvhtree = BVHTree.FromBMesh(bm)
    ob_eval.to_mesh_clear()
    return bvhtree

def check_mesh_faces(ob):
    me = ob.data
    if len(me.polygons) > 0:
        return True

    return False


class IvyGen(Operator):
    bl_idname = "curve.ivy_gen"
    bl_label = "IvyGen"
    bl_description = "Generate Ivy on an Mesh Object"
    bl_options = {'REGISTER', 'UNDO'}

    updateIvy: BoolProperty(
        name="Update Ivy",
        description="Update the Ivy location based on the cursor and Panel settings",
        default=False
    )
    defaultIvy: BoolProperty(
        name="Default Ivy",
        options={"HIDDEN", "SKIP_SAVE"},
        default=False
    )

    @classmethod
    def poll(self, context):
        # Check if there's an object and whether it's a mesh
        ob = context.active_object
        return ((ob is not None) and
                (ob.type == 'MESH') and
                (context.mode == 'OBJECT'))

    def invoke(self, context, event):
        self.updateIvy = True
        return self.execute(context)

    def execute(self, context):
        # scene = context.scene
        ivyProps = context.window_manager.ivy_gen_props

        if not self.updateIvy:
            return {'PASS_THROUGH'}

        # assign the variables, check if it is default
        # Note: update the values if window_manager props defaults are changed
        randomSeed = ivyProps.randomSeed if not self.defaultIvy else 0
        maxTime = ivyProps.maxTime if not self.defaultIvy else 0
        maxIvyLength = ivyProps.maxIvyLength if not self.defaultIvy else 1.0
        ivySize = ivyProps.ivySize if not self.defaultIvy else 0.02
        maxFloatLength = ivyProps.maxFloatLength if not self.defaultIvy else 0.5
        maxAdhesionDistance = ivyProps.maxAdhesionDistance if not self.defaultIvy else 1.0
        primaryWeight = ivyProps.primaryWeight if not self.defaultIvy else 0.5
        randomWeight = ivyProps.randomWeight if not self.defaultIvy else 0.2
        gravityWeight = ivyProps.gravityWeight if not self.defaultIvy else 1.0
        adhesionWeight = ivyProps.adhesionWeight if not self.defaultIvy else 0.1
        branchingProbability = ivyProps.branchingProbability if not self.defaultIvy else 0.05
        leafProbability = ivyProps.leafProbability if not self.defaultIvy else 0.35
        ivyBranchSize = ivyProps.ivyBranchSize if not self.defaultIvy else 0.001
        ivyLeafSize = ivyProps.ivyLeafSize if not self.defaultIvy else 0.02
        growLeaves = ivyProps.growLeaves if not self.defaultIvy else True

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # Get the selected object
        ob = context.active_object
        bvhtree = bvhtree_from_object(ob)

        # Check if the mesh has at least one polygon since some functions
        # are expecting them in the object's data (see T51753)
        check_face = check_mesh_faces(ob)
        if check_face is False:
            self.report({'WARNING'},
                        "Mesh Object doesn't have at least one Face. "
                        "Operation Cancelled")
            return {"CANCELLED"}

        # Compute bounding sphere radius
        # radius = computeBoundingSphere(ob)  # Not needed anymore

        # Get the seeding point
        seedPoint = context.scene.cursor.location

        # Fix the random seed
        rand_seed(randomSeed)

        # Make the new ivy
        IVY = Ivy(
            primaryWeight=primaryWeight,
            randomWeight=randomWeight,
            gravityWeight=gravityWeight,
            adhesionWeight=adhesionWeight,
            branchingProbability=branchingProbability,
            leafProbability=leafProbability,
            ivySize=ivySize,
            ivyLeafSize=ivyLeafSize,
            ivyBranchSize=ivyBranchSize,
            maxFloatLength=maxFloatLength,
            maxAdhesionDistance=maxAdhesionDistance
            )
        # Generate first root and node
        IVY.seed(seedPoint)

        checkTime = False
        maxLength = maxIvyLength  # * radius

        # If we need to check time set the flag
        if maxTime != 0.0:
            checkTime = True

        t = time.time()
        startPercent = 0.0
        checkAliveIter = [True, ]

        # Grow until 200 roots is reached or backup counter exceeds limit
        while (any(checkAliveIter) and
               (IVY.maxLength < maxLength) and
               (not checkTime or (time.time() - t < maxTime))):
            # Grow the ivy for this iteration
            IVY.grow(ob, bvhtree)

            # Print the proportion of ivy growth to console
            if (IVY.maxLength / maxLength * 100) > 10 * startPercent // 10:
                print('%0.2f%% of Ivy nodes have grown' %
                                         (IVY.maxLength / maxLength * 100))
                startPercent += 10
                if IVY.maxLength / maxLength > 1:
                    print("Halting Growth")

            # Make an iterator to check if all are alive
            checkAliveIter = (r.alive for r in IVY.ivyRoots)

        # Create the curve and leaf geometry
        createIvyGeometry(IVY, growLeaves)
        print("Geometry Generation Complete")

        print("Ivy generated in %0.2f s" % (time.time() - t))

        self.updateIvy = False
        self.defaultIvy = False

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "updateIvy", icon="FILE_REFRESH")


class CURVE_PT_IvyGenPanel(Panel):
    bl_label = "Ivy Generator"
    bl_idname = "CURVE_PT_IvyGenPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Create"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        col = layout.column(align=True)

        prop_new = col.operator("curve.ivy_gen", text="Add New Ivy", icon="OUTLINER_OB_CURVE")
        prop_new.defaultIvy = False
        prop_new.updateIvy = True

        prop_def = col.operator("curve.ivy_gen", text="Add New Default Ivy", icon="CURVE_DATA")
        prop_def.defaultIvy = True
        prop_def.updateIvy = True

        col = layout.column(align=True)
        col.label(text="Generation Settings:")
        col.prop(wm.ivy_gen_props, "randomSeed")
        col.prop(wm.ivy_gen_props, "maxTime")

        col = layout.column(align=True)
        col.label(text="Size Settings:")
        col.prop(wm.ivy_gen_props, "maxIvyLength")
        col.prop(wm.ivy_gen_props, "ivySize")
        col.prop(wm.ivy_gen_props, "maxFloatLength")
        col.prop(wm.ivy_gen_props, "maxAdhesionDistance")

        col = layout.column(align=True)
        col.label(text="Weight Settings:")
        col.prop(wm.ivy_gen_props, "primaryWeight")
        col.prop(wm.ivy_gen_props, "randomWeight")
        col.prop(wm.ivy_gen_props, "gravityWeight")
        col.prop(wm.ivy_gen_props, "adhesionWeight")

        col = layout.column(align=True)
        col.label(text="Branch Settings:")
        col.prop(wm.ivy_gen_props, "branchingProbability")
        col.prop(wm.ivy_gen_props, "ivyBranchSize")

        col = layout.column(align=True)
        col.prop(wm.ivy_gen_props, "growLeaves")

        if wm.ivy_gen_props.growLeaves:
            col = layout.column(align=True)
            col.label(text="Leaf Settings:")
            col.prop(wm.ivy_gen_props, "ivyLeafSize")
            col.prop(wm.ivy_gen_props, "leafProbability")


class IvyGenProperties(PropertyGroup):
    maxIvyLength: FloatProperty(
        name="Max Ivy Length",
        description="Maximum ivy length in Blender Units",
        default=1.0,
        min=0.0,
        soft_max=3.0,
        subtype='DISTANCE',
        unit='LENGTH'
    )
    primaryWeight: FloatProperty(
        name="Primary Weight",
        description="Weighting given to the current direction",
        default=0.5,
        min=0.0,
        soft_max=1.0
    )
    randomWeight: FloatProperty(
        name="Random Weight",
        description="Weighting given to the random direction",
        default=0.2,
        min=0.0,
        soft_max=1.0
    )
    gravityWeight: FloatProperty(
        name="Gravity Weight",
        description="Weighting given to the gravity direction",
        default=1.0,
        min=0.0,
        soft_max=1.0
    )
    adhesionWeight: FloatProperty(
        name="Adhesion Weight",
        description="Weighting given to the adhesion direction",
        default=0.1,
        min=0.0,
        soft_max=1.0
    )
    branchingProbability: FloatProperty(
        name="Branching Probability",
        description="Probability of a new branch forming",
        default=0.05,
        min=0.0,
        soft_max=1.0
    )
    leafProbability: FloatProperty(
        name="Leaf Probability",
        description="Probability of a leaf forming",
        default=0.35,
        min=0.0,
        soft_max=1.0
    )
    ivySize: FloatProperty(
        name="Ivy Size",
        description="The length of an ivy segment in Blender"
                    " Units",
        default=0.02,
        min=0.0,
        soft_max=1.0,
        precision=3
    )
    ivyLeafSize: FloatProperty(
        name="Ivy Leaf Size",
        description="The size of the ivy leaves",
        default=0.02,
        min=0.0,
        soft_max=0.5,
        precision=3
    )
    ivyBranchSize: FloatProperty(
        name="Ivy Branch Size",
        description="The size of the ivy branches",
        default=0.001,
        min=0.0,
        soft_max=0.1,
        precision=4
    )
    maxFloatLength: FloatProperty(
        name="Max Float Length",
        description="The maximum distance that a branch "
                    "can live while floating",
        default=0.5,
        min=0.0,
        soft_max=1.0
    )
    maxAdhesionDistance: FloatProperty(
        name="Max Adhesion Length",
        description="The maximum distance that a branch "
                    "will feel the effects of adhesion",
        default=1.0,
        min=0.0,
        soft_max=2.0,
        precision=2
    )
    randomSeed: IntProperty(
        name="Random Seed",
        description="The seed governing random generation",
        default=0,
        min=0
    )
    maxTime: FloatProperty(
        name="Maximum Time",
        description="The maximum time to run the generation for "
                    "in seconds generation (0.0 = Disabled)",
        default=0.0,
        min=0.0,
        soft_max=10
    )
    growLeaves: BoolProperty(
        name="Grow Leaves",
        description="Grow leaves or not",
        default=True
    )


classes = (
    IvyGen,
    IvyGenProperties,
    CURVE_PT_IvyGenPanel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.ivy_gen_props = PointerProperty(
        type=IvyGenProperties
    )


def unregister():
    del bpy.types.WindowManager.ivy_gen_props

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
