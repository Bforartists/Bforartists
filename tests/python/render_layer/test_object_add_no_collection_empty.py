# ############################################################
# Importing - Same For All Render Layer Tests
# ############################################################

import unittest
import os
import sys

from render_layer_common import *


# ############################################################
# Testing
# ############################################################

class UnitTesting(RenderLayerTesting):
    def test_syncing_object_add_empty(self):
        """
        See if new objects are added to the correct collection
        bpy.ops.object.add()
        """
        self.do_object_add_no_collection('EMPTY')


# ############################################################
# Main - Same For All Render Layer Tests
# ############################################################

if __name__ == '__main__':
    UnitTesting._extra_arguments = setup_extra_arguments(__file__)
    unittest.main()
