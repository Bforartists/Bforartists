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

"""
This script can import a HiRISE DTM .IMG file.
"""

import bpy
from bpy.props import *

from struct import pack, unpack
import os
import queue, threading

class image_properties:
    """ keeps track of image attributes throughout the hirise_dtm_importer class """
    def __init__(self, name, dimensions, pixel_scale):
      self.name( name )
      self.dims( dimensions )
      self.processed_dims( dimensions )
      self.pixel_scale( pixel_scale )

    def dims(self, dims=None):
      if dims is not None:
        self.__dims = dims
      return self.__dims

    def processed_dims(self, processed_dims=None):
      if processed_dims is not None:
        self.__processed_dims = processed_dims
      return self.__processed_dims

    def name(self, name=None):
      if name is not None:
        self.__name = name
      return self.__name

    def pixel_scale(self, pixel_scale=None):
      if pixel_scale is not None:
        self.__pixel_scale = pixel_scale
      return self.__pixel_scale

class hirise_dtm_importer(object):
    """ methods to understand/import a HiRISE DTM formatted as a PDS .IMG """

    def __init__(self, context, filepath):
      self.__context = context
      self.__filepath = filepath
      self.__ignore_value = 0x00000000
      self.__bin_mode = 'BIN6'
      self.scale( 1.0 )
      self.__cropXY = False

    def bin_mode(self, bin_mode=None):
      if bin_mode != None:
        self.__bin_mode = bin_mode
      return self.__bin_mode

    def scale(self, scale=None):
      if scale is not None:
        self.__scale = scale
      return self.__scale

    def crop(self, widthX, widthY, offX, offY):
      self.__cropXY = [ widthX, widthY, offX, offY ]
      return self.__cropXY

    ############################################################################
    ## PDS Label Operations
    ############################################################################

    def parsePDSLabel(self, labelIter, currentObjectName=None, level = ""):
      # Let's parse this thing... semi-recursively
      ## I started writing this caring about everything in the PDS standard but ...
      ## it's a mess and I only need a few things -- thar be hacks below
      ## Mostly I just don't care about continued data from previous lines
      label_structure = []

      # When are we done with this level?
      endStr = "END"
      if not currentObjectName is None:
        endStr = "END_OBJECT = %s" % currentObjectName
      line = ""

      while not line.rstrip() == endStr:
        line = next(labelIter)

        # Get rid of comments
        comment = line.find("/*")
        if comment > -1:
          line = line[:comment]

        # Take notice of objects
        if line[:8] == "OBJECT =":
          objName = line[8:].rstrip()
          label_structure.append(
            (
             objName.lstrip().rstrip(),
             self.parsePDSLabel(labelIter, objName.lstrip().rstrip(), level + "  ")
            )
          )
        elif line.find("END_OBJECT =") > -1:
          pass
        elif len(line.rstrip().lstrip()) > 0:
          key_val = line.split(" = ", 2)
          if len(key_val) == 2:
            label_structure.append( (key_val[0].rstrip().lstrip(), key_val[1].rstrip().lstrip()) )

      return label_structure

    # There has got to be a better way in python?
    def iterArr(self, label):
      for line in label:
        yield line

    def getPDSLabel(self, img):
      # Just takes file and stores it into an array for later use
      label = []
      done = False;
      # Grab label into array of lines
      while not done:
        line = str(img.readline(), 'utf-8')
        if line.rstrip() == "END":
          done = True
        label.append(line)
      return (label, self.parsePDSLabel(self.iterArr(label)))

    def getLinesAndSamples(self, label):
      """ uses the parsed PDS Label to get the LINES and LINE_SAMPLES parameters
          from the first object named "IMAGE" -- is hackish
      """
      for obj in label:
        if obj[0] == "IMAGE":
          return self.getLinesAndSamples(obj[1])
        if obj[0] == "LINES":
          lines = int(obj[1])
        if obj[0] == "LINE_SAMPLES":
          line_samples = int(obj[1])

      return ( line_samples, lines )

    def getValidMinMax(self, label):
      """ uses the parsed PDS Label to get the VALID_MINIMUM and VALID_MAXIMUM parameters
          from the first object named "IMAGE" -- is hackish
      """
      for obj in label:
        if obj[0] == "IMAGE":
          return self.getValidMinMax(obj[1])
        if obj[0] == "VALID_MINIMUM":
          vmin = float(obj[1])
        if obj[0] == "VALID_MAXIMUM":
          vmax = float(obj[1])

      return vmin, vmax

    def getMissingConstant(self, label):
      """ uses the parsed PDS Label to get the MISSING_CONSTANT parameter
          from the first object named "IMAGE" -- is hackish
      """
      for obj in label:
        if obj[0] == "IMAGE":
          return self.getMissingConstant(obj[1])
        if obj[0] == "MISSING_CONSTANT":
          bit_string_repr = obj[1]

      # This is always the same for a HiRISE image, so we are just checking it
      # to be a little less insane here. If someone wants to support another
      # constant then go for it. Just make sure this one continues to work too
      pieces = bit_string_repr.split("#")
      if pieces[0] == "16" and pieces[1] == "FF7FFFFB":
        ignore_value = unpack("f", pack("I", 0xFF7FFFFB))[0]

      return ( ignore_value )

    ############################################################################
    ## Image operations
    ############################################################################

    def bin2(self, image_iter, bin2_method_type="SLOW"):
      """ this is an iterator that: Given an image iterator will yield binned lines """

      ignore_value = self.__ignore_value

      img_props = next(image_iter)
      # dimensions shrink as we remove pixels
      processed_dims = img_props.processed_dims()
      processed_dims = ( processed_dims[0]//2, processed_dims[1]//2 )
      img_props.processed_dims( processed_dims )
      # each pixel is larger as binning gets larger
      pixel_scale = img_props.pixel_scale()
      pixel_scale = ( pixel_scale[0]*2, pixel_scale[1]*2 )
      img_props.pixel_scale( pixel_scale )
      yield img_props

      # Take two lists  [a1, a2, a3], [b1, b2, b3] and combine them into one
      # list of [a1 + b1, a2+b2,  ... ] as long as both values are not ignorable
      combine_fun = lambda a, b: a != ignore_value and b != ignore_value and (a + b)/2 or ignore_value

      line_count = 0
      ret_list = []
      for line in image_iter:
        if line_count == 1:
          line_count = 0
          tmp_list = list(map(combine_fun, line, last_line))
          while len(tmp_list) > 1:
            ret_list.append( combine_fun( tmp_list[0], tmp_list[1] ) )
            del tmp_list[0:2]
          yield ret_list
          ret_list = []
        else:
          last_line = line
          line_count += 1

    def bin6(self, image_iter, bin6_method_type="SLOW"):
      """ this is an iterator that: Given an image iterator will yield binned lines """

      img_props = next(image_iter)
      # dimensions shrink as we remove pixels
      processed_dims = img_props.processed_dims()
      processed_dims = ( processed_dims[0]//6, processed_dims[1]//6 )
      img_props.processed_dims( processed_dims )
      # each pixel is larger as binning gets larger
      pixel_scale = img_props.pixel_scale()
      pixel_scale = ( pixel_scale[0]*6, pixel_scale[1]*6 )
      img_props.pixel_scale( pixel_scale )
      yield img_props

      if bin6_method_type == "FAST":
        bin6_method = self.bin6_real_fast
      else:
        bin6_method = self.bin6_real

      raw_data = []
      line_count = 0
      for line in image_iter:
        raw_data.append( line )
        line_count += 1
        if line_count == 6:
          yield bin6_method( raw_data )
          line_count = 0
          raw_data = []

    def bin6_real(self, raw_data):
      """ does a 6x6 sample of raw_data and returns a single line of data """
      # TODO: make this more efficient

      binned_data = []

      # Filter out those unwanted hugely negative values...
      IGNORE_VALUE = self.__ignore_value

      base = 0
      for i in range(0, len(raw_data[0])//6):

        ints = (raw_data[0][base:base+6] +
          raw_data[1][base:base+6] +
          raw_data[2][base:base+6] +
          raw_data[3][base:base+6] +
          raw_data[4][base:base+6] +
          raw_data[5][base:base+6] )

        ints = [num for num in ints if num != IGNORE_VALUE]

        # If we have all pesky values, return a pesky value
        if not ints:
          binned_data.append( IGNORE_VALUE )
        else:
          binned_data.append( sum(ints, 0.0) / len(ints) )

        base += 6

      return binned_data

    def bin6_real_fast(self, raw_data):
      """ takes a single value from each 6x6 sample of raw_data and returns a single line of data """
      # TODO: make this more efficient

      binned_data = []

      base = 0
      for i in range(0, len(raw_data[0])//6):
        binned_data.append( raw_data[0][base] )
        base += 6

      return binned_data

    def bin12(self, image_iter, bin12_method_type="SLOW"):
      """ this is an iterator that: Given an image iterator will yield binned lines """

      img_props = next(image_iter)
      # dimensions shrink as we remove pixels
      processed_dims = img_props.processed_dims()
      processed_dims = ( processed_dims[0]//12, processed_dims[1]//12 )
      img_props.processed_dims( processed_dims )
      # each pixel is larger as binning gets larger
      pixel_scale = img_props.pixel_scale()
      pixel_scale = ( pixel_scale[0]*12, pixel_scale[1]*12 )
      img_props.pixel_scale( pixel_scale )
      yield img_props

      if bin12_method_type == "FAST":
        bin12_method = self.bin12_real_fast
      else:
        bin12_method = self.bin12_real

      raw_data = []
      line_count = 0
      for line in image_iter:
        raw_data.append( line )
        line_count += 1
        if line_count == 12:
          yield bin12_method( raw_data )
          line_count = 0
          raw_data = []

    def bin12_real(self, raw_data):
      """ does a 12x12 sample of raw_data and returns a single line of data """

      binned_data = []

      # Filter out those unwanted hugely negative values...
      filter_fun = lambda a: self.__ignore_value.__ne__(a)

      base = 0
      for i in range(0, len(raw_data[0])//12):

        ints = list(filter( filter_fun, raw_data[0][base:base+12] +
          raw_data[1][base:base+12] +
          raw_data[2][base:base+12] +
          raw_data[3][base:base+12] +
          raw_data[4][base:base+12] +
          raw_data[5][base:base+12] +
          raw_data[6][base:base+12] +
          raw_data[7][base:base+12] +
          raw_data[8][base:base+12] +
          raw_data[9][base:base+12] +
          raw_data[10][base:base+12] +
          raw_data[11][base:base+12] ))
        len_ints = len( ints )

        # If we have all pesky values, return a pesky value
        if len_ints == 0:
          binned_data.append( self.__ignore_value )
        else:
          binned_data.append( sum(ints) / len(ints) )

        base += 12
      return binned_data

    def bin12_real_fast(self, raw_data):
      """ takes a single value from each 12x12 sample of raw_data and returns a single line of data """
      return raw_data[0][11::12]

    def cropXY(self, image_iter, XSize=None, YSize=None, XOffset=0, YOffset=0):
      """ return a cropped portion of the image """

      img_props = next(image_iter)
      # dimensions shrink as we remove pixels
      processed_dims = img_props.processed_dims()

      if XSize is None:
        XSize = processed_dims[0]
      if YSize is None:
        YSize = processed_dims[1]

      if XSize + XOffset > processed_dims[0]:
        XSize = processed_dims[0]
        XOffset = 0
      if YSize + YOffset > processed_dims[1]:
        YSize = processed_dims[1]
        YOffset = 0

      img_props.processed_dims( (XSize, YSize) )
      yield img_props

      currentY = 0
      for line in image_iter:
        if currentY >= YOffset and currentY <= YOffset + YSize:
          yield line[XOffset:XOffset+XSize]
        # Not much point in reading the rest of the data...
        if currentY == YOffset + YSize:
          return
        currentY += 1

    def getImage(self, img, img_props):
      """ Assumes 32-bit pixels -- bins image """
      dims = img_props.dims()

      # setup to unpack more efficiently.
      x_len = dims[0]
      # little endian (PC_REAL)
      unpack_str = "<"
      # unpack_str = ">"
      unpack_bytes_str = "<"
      pack_bytes_str = "="
      # 32 bits/sample * samples/line = y_bytes (per line)
      x_bytes = 4*x_len
      for x in range(0, x_len):
        # 32-bit float is "d"
        unpack_str += "f"
        unpack_bytes_str += "I"
        pack_bytes_str += "I"

      # Each iterator yields this first ... it is for reference of the next iterator:
      yield img_props

      for y in range(0, dims[1]):
        # pixels is a byte array
        pixels = b''
        while len(pixels) < x_bytes:
          new_pixels = img.read( x_bytes - len(pixels) )
          pixels += new_pixels
          if len(new_pixels) == 0:
            x_bytes = -1
            pixels = []
        if len(pixels) == x_bytes:
          if 0 == 1:
            repacked_pixels = b''
            for integer in unpack(unpack_bytes_str, pixels):
              repacked_pixels += pack("=I", integer)
            yield unpack( unpack_str, repacked_pixels )
          else:
            yield unpack( unpack_str, pixels )

    def shiftToOrigin(self, image_iter, image_min_max):
      """ takes a generator and shifts the points by the valid minimum
          also removes points with value self.__ignore_value and replaces them with None
      """

      # use the passed in values ...
      valid_min = image_min_max[0]

      # pass on dimensions/pixel_scale since we don't modify them here
      yield next(image_iter)


      # closures rock!
      def normalize_fun(point):
        if point == self.__ignore_value:
          return None
        return point - valid_min

      for line in image_iter:
        yield list(map(normalize_fun, line))

    def scaleZ(self, image_iter, scale_factor):
      """ scales the mesh values by a factor """
      # pass on dimensions since we don't modify them here
      yield next(image_iter)

      scale_factor = self.scale()

      def scale_fun(point):
        try:
          return point * scale_factor
        except:
          return None

      for line in image_iter:
        yield list(map(scale_fun, line))

    def genMesh(self, image_iter):
      """Returns a mesh object from an image iterator this has the
         value-added feature that a value of "None" is ignored
      """

      # Get the output image size given the above transforms
      img_props = next(image_iter)

      # Let's interpolate the binned DTM with blender -- yay meshes!
      coords = []
      faces  = []
      face_count = 0
      coord = -1
      max_x = img_props.processed_dims()[0]
      max_y = img_props.processed_dims()[1]

      scale_x = self.scale() * img_props.pixel_scale()[0]
      scale_y = self.scale() * img_props.pixel_scale()[1]

      line_count = 0
      # seed the last line (or previous line) with a line
      last_line = next(image_iter)
      point_offset = 0
      previous_point_offset = 0

      # Let's add any initial points that are appropriate
      x = 0
      point_offset += len( last_line ) - last_line.count(None)
      for z in last_line:
        if z != None:
          coords.append( (x*scale_x, 0.0, z) )
          coord += 1
        x += 1

      # We want to ignore points with a value of "None" but we also need to create vertices
      # with an index that we can re-create on the next line. The solution is to remember
      # two offsets: the point offset and the previous point offset.
      #   these offsets represent the point index that blender gets -- not the number of
      #   points we have read from the image

      # if "x" represents points that are "None" valued then conceptually this is how we
      # think of point indices:
      #
      # previous line: offset0   x   x  +1  +2  +3
      # current line:  offset1   x  +1  +2  +3   x

      # once we can map points we can worry about making triangular or square faces to fill
      # the space between vertices so that blender is more efficient at managing the final
      # structure.

      # read each new line and generate coordinates+faces
      for dtm_line in image_iter:

        # Keep track of where we are in the image
        line_count += 1
        y_val = line_count*-scale_y

        # Just add all points blindly
        # TODO: turn this into a map
        x = 0
        for z in dtm_line:
          if z != None:
            coords.append( (x*scale_x, y_val, z) )
            coord += 1
          x += 1

        # Calculate faces
        for x in range(0, max_x - 1):
          vals = [
            last_line[ x + 1 ],
            last_line[ x ],
            dtm_line[  x ],
            dtm_line[  x + 1 ],
            ]

          # Two or more values of "None" means we can ignore this block
          none_val = vals.count(None)

          # Common case: we can create a square face
          if none_val == 0:
            faces.append( (
              previous_point_offset,
              previous_point_offset+1,
              point_offset+1,
              point_offset,
              ) )
            face_count += 1
          elif none_val == 1:
            # special case: we can implement a triangular face
            ## NB: blender 2.5 makes a triangular face when the last coord is 0
            # TODO: implement a triangular face
            pass

          if vals[1] != None:
            previous_point_offset += 1
          if vals[2] != None:
            point_offset += 1

        # Squeeze the last point offset increment out of the previous line
        if last_line[-1] != None:
          previous_point_offset += 1

        # Squeeze the last point out of the current line
        if dtm_line[-1] != None:
          point_offset += 1

        # remember what we just saw (and forget anything before that)
        last_line = dtm_line

      me = bpy.data.meshes.new(img_props.name()) # create a new mesh
      #from_pydata(self, vertices, edges, faces)
      #Make a mesh from a list of vertices/edges/faces
      #Until we have a nicer way to make geometry, use this.
      #:arg vertices:
      #   float triplets each representing (X, Y, Z)
      #   eg: [(0.0, 1.0, 0.5), ...].
      #:type vertices: iterable object
      #:arg edges:
      #   int pairs, each pair contains two indices to the
      #   *vertices* argument. eg: [(1, 2), ...]
      #:type edges: iterable object
      #:arg faces:
      #   iterator of faces, each faces contains three or more indices to
      #   the *vertices* argument. eg: [(5, 6, 8, 9), (1, 2, 3), ...]
      #:type faces: iterable object
      me.from_pydata(coords, [], faces)      

      # me.vertices.add(len(coords)/3)
      # me.vertices.foreach_set("co", coords)
      # me.faces.add(len(faces)/4)
      # me.faces.foreach_set("vertices_raw", faces)

      me.update()

      bin_desc = self.bin_mode()
      if bin_desc == 'NONE':
        bin_desc = 'No Bin'

      ob=bpy.data.objects.new("DTM - %s" % bin_desc, me)

      return ob

    ################################################################################
    #  Yay, done with importer functions ... let's see the abstraction in action!    #
    ################################################################################
    def execute(self):

      img = open(self.__filepath, 'rb')

      (label, parsedLabel) = self.getPDSLabel(img)

      image_dims = self.getLinesAndSamples(parsedLabel)
      img_min_max_vals = self.getValidMinMax(parsedLabel)
      self.__ignore_value = self.getMissingConstant(parsedLabel)


      # MAGIC VALUE? -- need to formalize this to rid ourselves of bad points
      img.seek(28)
      # Crop off 4 lines
      img.seek(4*image_dims[0])

      # HiRISE images (and most others?) have 1m x 1m pixels
      pixel_scale=(1, 1)

      # The image we are importing
      image_name = os.path.basename( self.__filepath )

      # Set the properties of the image in a manageable object
      img_props = image_properties( image_name, image_dims, pixel_scale )

      # Get an iterator to iterate over lines
      image_iter = self.getImage(img, img_props)

      ## Wrap the image_iter generator with other generators to modify the dtm on a
      ## line-by-line basis. This creates a stream of modifications instead of reading
      ## all of the data at once, processing all of the data (potentially several times)
      ## and then handing it off to blender
      ## TODO: find a way to alter projection based on transformations below

      if self.__cropXY:
        image_iter = self.cropXY(image_iter,
                                 XSize=self.__cropXY[0], 
                                 YSize=self.__cropXY[1],
                                 XOffset=self.__cropXY[2],
                                 YOffset=self.__cropXY[3]
        			 )

      # Select an appropriate binning mode
      ## TODO: generalize the binning fn's
      bin_mode = self.bin_mode()
      bin_mode_funcs = {
        'BIN2': self.bin2(image_iter),
        'BIN6': self.bin6(image_iter),
        'BIN6-FAST': self.bin6(image_iter, 'FAST'),
        'BIN12': self.bin12(image_iter),
        'BIN12-FAST': self.bin12(image_iter, 'FAST')
        }
      if bin_mode in bin_mode_funcs.keys():
        image_iter = bin_mode_funcs[ bin_mode ]

      image_iter = self.shiftToOrigin(image_iter, img_min_max_vals)

      if self.scale != 1.0:
        image_iter = self.scaleZ(image_iter, img_min_max_vals)

      # Create a new mesh object and set data from the image iterator
      ob_new = self.genMesh(image_iter)

      if img:
        img.close()

      # Add mesh object to the current scene
      scene = self.__context.scene
      scene.objects.link(ob_new)
      scene.update()

      # deselect other objects
      bpy.ops.object.select_all(action='DESELECT')

      # scene.objects.active = ob_new
      # Select the new mesh
      ob_new.select = True

      return ('FINISHED',)

def load(operator, context, filepath, scale, bin_mode, cropVars):
    print("Bin Mode: %s" % bin_mode)
    print("Scale: %f" % scale)
    importer = hirise_dtm_importer(context,filepath)
    importer.bin_mode( bin_mode )
    importer.scale( scale )
    if cropVars:
        importer.crop( cropVars[0], cropVars[1], cropVars[2], cropVars[3] )
    importer.execute()

    print("Loading %s" % filepath)
    return {'FINISHED'}
