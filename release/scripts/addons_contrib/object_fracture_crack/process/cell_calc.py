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

# <pep8 compliant>

# Script copyright (C) Blender Foundation 2012


def points_to_verts(original_xyz_minmax,
                    points,
                    points_scale=None,
                    margin_bounds=0.05,
                    margin_cell=0.0):

    from math import sqrt
    import mathutils
    from mathutils import Vector

    cells = []
    plane_indices = []
    vertices = []

    if points_scale is not None:
        points_scale = tuple(points_scale)
    if points_scale == (1.0, 1.0, 1.0):
        points_scale = None

    # there are many ways we could get planes - convex hull for eg
    # but it ends up fastest if we just use bounding box
    if 1:
        xmin, xmax = original_xyz_minmax["x"]
        ymin, ymax = original_xyz_minmax["y"]
        zmin, zmax = original_xyz_minmax["z"]
        
        xmin -= margin_bounds
        xmax += margin_bounds
        ymin -= margin_bounds
        ymax += margin_bounds
        zmin -= margin_bounds
        zmax += margin_bounds
        
        # (x,y,z,scaler) for plane. xyz is normaliized direction. scaler is scale for plane.
        # Plane will be made at the perpendicular direction of the normal vector.
        convexPlanes = [
            Vector((+1.0, 0.0, 0.0, -xmax)),
            Vector((-1.0, 0.0, 0.0, +xmin)),
            Vector((0.0, +1.0, 0.0, -ymax)),
            Vector((0.0, -1.0, 0.0, +ymin)),
            Vector((0.0, 0.0, +1.0, -zmax)),
            Vector((0.0, 0.0, -1.0, +zmin)),
            ]
      
    if len(points) > 1:
        points_dist_sorted = [(Vector(p[0]), p[1]) for p in points]
        
        for i, point_current in enumerate(points):
            planes = [None] * len(convexPlanes)
            for j in range(len(convexPlanes)):
                planes[j] = convexPlanes[j].copy()               
                # e.g. Dot product point's (xyz) with convex's (+1.0,0.0,0.0) detects x value of the point.
                # e.g. Then, x scaler += point's x value.
                planes[j][3] += planes[j].xyz.dot(point_current[0])
                       
            distance_max = 10000000000.0  # a big value!
            
            points_dist_sorted_current = points_dist_sorted.copy()
            # Closer points to the current point are earlier order. Of course, current point is the first.
            points_dist_sorted_current.sort(key=lambda p: (p[0] - point_current[0]).length_squared)
            
            # The point itself is removed.
            points_dist_sorted_current.pop(0)        
            
            # Compare the current point with other points.
            for j in range(len(points_dist_sorted_current)):

                point_target = points_dist_sorted_current[j]
                normal = 0           
                normal = point_target[0] - point_current[0]           
                nlength = normal.length # is sqrt(X^2+y^2+z^2).

                if points_scale is not None:
                    normal_alt = normal.copy()
                    normal_alt.x *= points_scale[0]
                    normal_alt.y *= points_scale[1]
                    normal_alt.z *= points_scale[2]

                    # -rotate plane to new distance
                    # -should always be positive!! - but abs incase
                    # Scale rate (normal_alt/normal). If these are the same, dot product is 1.
                    scalar = normal_alt.normalized().dot(normal.normalized())
                    # assert(scalar >= 0.0)
                    nlength *= scalar
                    normal = normal_alt

                if nlength > distance_max:
                    break

                # 4D vector, the same form as convexPlanes. (x,y,z,scaler).
                plane = normal.normalized()
                plane.resize_4d()
                plane[3] = (-nlength / 2.0) + margin_cell
                planes.append(plane)
                
                # Make vertex points of cell, by crossing point of planes.
                vertices[:], plane_indices[:] = mathutils.geometry.points_in_planes(planes)
                #if len(vertices) == 0:
                #    break

                if len(plane_indices) != len(planes):
                    planes[:] = [planes[k] for k in plane_indices]

                # for comparisons use length_squared and delay
                # converting to a real length until the end. 
                distance_max = 10000000000.0  # a big value!
                for v in vertices:
                    distance = v.length_squared
                    if distance_max < distance:
                        distance_max = distance
                distance_max = sqrt(distance_max)  # make real length　ここでルートでマックスを下げているのか？でも下で２倍にしているが。
                distance_max *= 2.0

            if len(vertices) == 0:
                continue
                
            cells.append((point_current[0], vertices[:]))
            del vertices[:]        
          
    else:
        vertices[:], plane_indices[:] = mathutils.geometry.points_in_planes(convexPlanes)
        #convex_center = Vector(((xmin-xmax)/2, (ymin-ymax)/2, (zmin-zmax)/2))
        convex_center = Vector((0,0,0))
        cells.append((convex_center, vertices[:]))
    
    return cells